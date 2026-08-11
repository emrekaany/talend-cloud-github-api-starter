from __future__ import annotations

import pytest

from talend_api_starter.errors import XmlSafetyError
from talend_api_starter.synthetic import (
    SYNTHETIC_ITEM,
    SYNTHETIC_PROPERTIES,
    synthetic_files,
)
from talend_api_starter.xmlsafe import inventory_talend_jobs, parse_talend_job

PROPERTIES_PATH = "process/demo/SyntheticCustomers_0.1.properties"
ITEM_PATH = "process/demo/SyntheticCustomers_0.1.item"


def test_synthetic_pair_is_linked_by_xmi_references_and_href() -> None:
    result = inventory_talend_jobs(synthetic_files())
    assert result.warnings == ()
    assert len(result.jobs) == 1
    job = result.jobs[0]
    assert job.label == "SyntheticCustomers"
    assert job.version == "0.1"
    assert job.status == "DEV"
    assert [component.component_type for component in job.components] == [
        "tFixedFlowInput",
        "tLogRow",
    ]
    assert [component.unique_name for component in job.components] == [
        "tFixedFlowInput_1",
        "tLogRow_1",
    ]


@pytest.mark.parametrize(
    "unsafe",
    [
        b'<!DOCTYPE x SYSTEM "file:///etc/passwd"><x />',
        b'<!ENTITY leak SYSTEM "file:///etc/passwd"><x>&leak;</x>',
        b'<!DoCtYpE x [<!EnTiTy x "boom">]><x>&x;</x>',
    ],
)
def test_dtd_and_entity_declarations_are_rejected(unsafe: bytes) -> None:
    with pytest.raises(XmlSafetyError, match="dtd_or_entity_rejected"):
        parse_talend_job(
            unsafe,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_utf16_cannot_bypass_declaration_filter() -> None:
    unsafe = '<!DOCTYPE x [<!ENTITY x "boom">]><x>&x;</x>'.encode("utf-16")
    with pytest.raises(XmlSafetyError, match="unsupported_encoding"):
        parse_talend_job(
            unsafe,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_xmi_reference_mismatch_is_rejected() -> None:
    altered = SYNTHETIC_PROPERTIES.replace(
        b'property="_synthetic_property"', b'property="_different_property"'
    )
    with pytest.raises(XmlSafetyError, match="xmi_pair_reference_mismatch"):
        parse_talend_job(
            altered,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_href_path_traversal_is_rejected() -> None:
    altered = SYNTHETIC_PROPERTIES.replace(
        b'href="SyntheticCustomers_0.1.item#/"',
        b'href="../SyntheticCustomers_0.1.item#/"',
    )
    with pytest.raises(XmlSafetyError, match="invalid_item_href"):
        parse_talend_job(
            altered,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_unknown_properties_and_item_roots_are_rejected() -> None:
    fake_properties = (
        b'<evil xmlns:xmi="http://www.omg.org/XMI">'
        b'<Property xmi:id="p" label="Fake" version="0.1" item="i" />'
        b'<ProcessItem xmi:id="i" property="p">'
        b'<process href="Fake_0.1.item#/" /></ProcessItem></evil>'
    )
    with pytest.raises(XmlSafetyError, match="unsupported_properties_root"):
        parse_talend_job(
            fake_properties,
            b"<evil><node componentName='made-up' /></evil>",
            properties_path="Fake_0.1.properties",
            item_path="Fake_0.1.item",
        )
    with pytest.raises(XmlSafetyError, match="unsupported_item_root"):
        parse_talend_job(
            SYNTHETIC_PROPERTIES,
            b"<evil><node componentName='made-up' /></evil>",
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_filename_version_relationship_is_validated() -> None:
    with pytest.raises(XmlSafetyError, match="properties_filename_version"):
        parse_talend_job(
            SYNTHETIC_PROPERTIES,
            SYNTHETIC_ITEM,
            properties_path="process/demo/SyntheticCustomers.properties",
            item_path=ITEM_PATH,
        )
    altered_properties = SYNTHETIC_PROPERTIES.replace(
        b'href="SyntheticCustomers_0.1.item#/"',
        b'href="SyntheticCustomers.item#/"',
    )
    with pytest.raises(XmlSafetyError, match="item_filename_version"):
        parse_talend_job(
            altered_properties,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path="process/demo/SyntheticCustomers.item",
        )


def test_xml_byte_budget_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("talend_api_starter.xmlsafe.MAX_XML_BYTES", 50)
    with pytest.raises(XmlSafetyError, match="byte_budget_exceeded"):
        parse_talend_job(
            SYNTHETIC_PROPERTIES,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_xml_depth_budget_is_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("talend_api_starter.xmlsafe.MAX_XML_DEPTH", 1)
    with pytest.raises(XmlSafetyError, match="depth_budget_exceeded"):
        parse_talend_job(
            SYNTHETIC_PROPERTIES,
            SYNTHETIC_ITEM,
            properties_path=PROPERTIES_PATH,
            item_path=ITEM_PATH,
        )


def test_bad_job_is_isolated_as_redacted_warning() -> None:
    files = synthetic_files()
    files[PROPERTIES_PATH] = b"<broken"
    result = inventory_talend_jobs(files)
    assert result.jobs == ()
    assert result.warnings == (f"{PROPERTIES_PATH}: properties_malformed_xml",)
    assert "<broken" not in result.warnings[0]


def test_two_properties_cannot_claim_the_same_item() -> None:
    files = synthetic_files()
    duplicate_path = "process/demo/Copy_0.1.properties"
    files[duplicate_path] = SYNTHETIC_PROPERTIES
    result = inventory_talend_jobs(files)
    assert result.jobs == ()
    assert len(result.warnings) == 2
    assert all("ambiguous_item_reference" in warning for warning in result.warnings)
