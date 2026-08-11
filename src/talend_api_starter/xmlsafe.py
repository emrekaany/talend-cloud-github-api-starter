"""Bounded Talend XMI parsing without DTD or entity support."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from .errors import XmlSafetyError

MAX_XML_BYTES = 1_000_000
MAX_XML_NODES = 10_000
MAX_XML_DEPTH = 64
MAX_XML_ATTRIBUTES = 40_000
MAX_XML_TEXT_BYTES = 1_000_000
MAX_COMPONENTS = 2_000

XMI_NAMESPACE = "http://www.omg.org/XMI"
TALEND_PROPERTIES_NAMESPACE = "http://www.talend.org/properties"
TALEND_FILE_NAMESPACE = "platform:/resource/org.talend.model/model/TalendFile.xsd"

_XMI_ROOT = f"{{{XMI_NAMESPACE}}}XMI"
_XMI_ID_ATTRIBUTE = f"{{{XMI_NAMESPACE}}}id"
_PROPERTY_TAG = f"{{{TALEND_PROPERTIES_NAMESPACE}}}Property"
_PROCESS_ITEM_TAG = f"{{{TALEND_PROPERTIES_NAMESPACE}}}ProcessItem"
_PROCESS_ROOT = f"{{{TALEND_FILE_NAMESPACE}}}ProcessType"
_FORBIDDEN_DECLARATION_RE = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", re.I)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")


@dataclass(frozen=True, slots=True)
class ComponentDescriptor:
    component_type: str
    unique_name: str | None


@dataclass(frozen=True, slots=True)
class JobDescriptor:
    label: str
    version: str
    status: str | None
    properties_path: str
    item_path: str
    components: tuple[ComponentDescriptor, ...]


@dataclass(frozen=True, slots=True)
class InventoryResult:
    jobs: tuple[JobDescriptor, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _PropertiesDescriptor:
    label: str
    version: str
    status: str | None
    item_href: str


def _xmi_id(element: ET.Element) -> str | None:
    return element.get(_XMI_ID_ATTRIBUTE)


def _safe_display(value: str, field: str, max_length: int = 256) -> str:
    value = value.strip()
    if not value or len(value) > max_length or _CONTROL_RE.search(value):
        raise XmlSafetyError(f"invalid_{field}")
    return value


def _parse_bounded_xml(content: bytes, document_kind: str) -> ET.Element:
    if len(content) > MAX_XML_BYTES:
        raise XmlSafetyError(f"{document_kind}_byte_budget_exceeded")
    if b"\x00" in content:
        raise XmlSafetyError(f"{document_kind}_unsupported_encoding")
    if _FORBIDDEN_DECLARATION_RE.search(content):
        raise XmlSafetyError(f"{document_kind}_dtd_or_entity_rejected")
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise XmlSafetyError(f"{document_kind}_malformed_xml") from None

    node_count = 0
    attribute_count = 0
    text_bytes = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        node_count += 1
        attribute_count += len(element.attrib)
        text_bytes += len((element.text or "").encode("utf-8"))
        text_bytes += len((element.tail or "").encode("utf-8"))
        if node_count > MAX_XML_NODES:
            raise XmlSafetyError(f"{document_kind}_node_budget_exceeded")
        if depth > MAX_XML_DEPTH:
            raise XmlSafetyError(f"{document_kind}_depth_budget_exceeded")
        if attribute_count > MAX_XML_ATTRIBUTES:
            raise XmlSafetyError(f"{document_kind}_attribute_budget_exceeded")
        if text_bytes > MAX_XML_TEXT_BYTES:
            raise XmlSafetyError(f"{document_kind}_text_budget_exceeded")
        stack.extend((child, depth + 1) for child in element)
    return root


def _validate_relative_href(href: str) -> str:
    href = href.split("#", 1)[0].strip()
    parsed = urlsplit(href)
    if (
        not href
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or href.startswith("/")
        or href.endswith("/")
        or "\\" in href
        or "//" in href
    ):
        raise XmlSafetyError("invalid_item_href")
    path = PurePosixPath(href)
    if any(part in ("", ".", "..") for part in path.parts):
        raise XmlSafetyError("invalid_item_href")
    if path.suffix != ".item":
        raise XmlSafetyError("invalid_item_href")
    return path.as_posix()


def _parse_properties(content: bytes) -> _PropertiesDescriptor:
    root = _parse_bounded_xml(content, "properties")
    if root.tag != _XMI_ROOT:
        raise XmlSafetyError("unsupported_properties_root")
    properties = list(root.iter(_PROPERTY_TAG))
    process_items = list(root.iter(_PROCESS_ITEM_TAG))
    if len(properties) != 1 or len(process_items) != 1:
        raise XmlSafetyError("expected_one_property_and_process_item")
    prop = properties[0]
    process_item = process_items[0]
    prop_xmi_id = _xmi_id(prop)
    item_xmi_id = _xmi_id(process_item)
    if not prop_xmi_id or not item_xmi_id:
        raise XmlSafetyError("missing_xmi_identity")

    property_ref = (process_item.get("property") or "").lstrip("#")
    item_ref = (prop.get("item") or "").lstrip("#")
    if property_ref != prop_xmi_id or item_ref != item_xmi_id:
        raise XmlSafetyError("xmi_pair_reference_mismatch")

    process_links = [
        child for child in process_item if child.tag == "process" and child.get("href")
    ]
    if len(process_links) != 1:
        raise XmlSafetyError("expected_one_process_href")
    label = _safe_display(prop.get("label", ""), "job_label")
    version = _safe_display(prop.get("version", ""), "job_version", 64)
    if not _VERSION_RE.fullmatch(version):
        raise XmlSafetyError("unsupported_job_version")
    status_raw = prop.get("statusCode")
    status = (
        _safe_display(status_raw, "job_status", 64) if status_raw is not None else None
    )
    href = _validate_relative_href(process_links[0].get("href", ""))
    return _PropertiesDescriptor(label, version, status, href)


def _parse_components(content: bytes) -> tuple[ComponentDescriptor, ...]:
    root = _parse_bounded_xml(content, "item")
    if root.tag != _PROCESS_ROOT:
        raise XmlSafetyError("unsupported_item_root")
    components: list[ComponentDescriptor] = []
    for element in root.iter():
        if element.tag != "node":
            continue
        component_type = _safe_display(
            element.get("componentName", ""), "component_type", 128
        )
        unique_name: str | None = None
        for candidate in element.iter():
            if (
                candidate.tag == "elementParameter"
                and candidate.get("name") == "UNIQUE_NAME"
            ):
                raw = candidate.get("value")
                if raw:
                    unique_name = _safe_display(raw, "component_name", 128)
                break
        components.append(ComponentDescriptor(component_type, unique_name))
        if len(components) > MAX_COMPONENTS:
            raise XmlSafetyError("component_budget_exceeded")
    return tuple(components)


def parse_talend_job(
    properties_content: bytes,
    item_content: bytes,
    *,
    properties_path: str = "SyntheticJob_0.1.properties",
    item_path: str = "SyntheticJob_0.1.item",
) -> JobDescriptor:
    properties = _parse_properties(properties_content)
    expected_item = (
        PurePosixPath(properties_path).parent / PurePosixPath(properties.item_href)
    ).as_posix()
    if expected_item.startswith("./"):
        expected_item = expected_item[2:]
    if expected_item != item_path:
        raise XmlSafetyError("properties_item_path_mismatch")
    if not PurePosixPath(properties_path).name.endswith(
        f"_{properties.version}.properties"
    ):
        raise XmlSafetyError("properties_filename_version_mismatch")
    if not PurePosixPath(item_path).name.endswith(f"_{properties.version}.item"):
        raise XmlSafetyError("item_filename_version_mismatch")
    return JobDescriptor(
        label=properties.label,
        version=properties.version,
        status=properties.status,
        properties_path=properties_path,
        item_path=item_path,
        components=_parse_components(item_content),
    )


def inventory_talend_jobs(files: Mapping[str, bytes]) -> InventoryResult:
    """Pair descriptors by their XMI href; isolate malformed jobs as warnings."""

    if len(files) > 2_000:
        raise XmlSafetyError("file_inventory_budget_exceeded")
    jobs: list[JobDescriptor] = []
    warnings: list[str] = []
    candidates: list[tuple[str, str]] = []
    for properties_path in sorted(
        path for path in files if path.endswith(".properties")
    ):
        try:
            properties = _parse_properties(files[properties_path])
            item_path = (
                PurePosixPath(properties_path).parent
                / PurePosixPath(properties.item_href)
            ).as_posix()
            if item_path.startswith("./"):
                item_path = item_path[2:]
            candidates.append((properties_path, item_path))
        except XmlSafetyError as exc:
            # Paths are repository-relative and validated by the GitHub client;
            # raw XML and exception internals never enter warnings.
            warnings.append(f"{properties_path}: {exc}")

    item_references: dict[str, list[str]] = {}
    for properties_path, item_path in candidates:
        item_references.setdefault(item_path, []).append(properties_path)

    for properties_path, item_path in candidates:
        if len(item_references[item_path]) != 1:
            warnings.append(f"{properties_path}: ambiguous_item_reference")
            continue
        item_content = files.get(item_path)
        if item_content is None:
            warnings.append(f"{properties_path}: referenced_item_missing")
            continue
        try:
            jobs.append(
                parse_talend_job(
                    files[properties_path],
                    item_content,
                    properties_path=properties_path,
                    item_path=item_path,
                )
            )
        except XmlSafetyError as exc:
            warnings.append(f"{properties_path}: {exc}")
    return InventoryResult(tuple(jobs), tuple(warnings))


def component_types(jobs: Iterable[JobDescriptor]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {component.component_type for job in jobs for component in job.components}
        )
    )
