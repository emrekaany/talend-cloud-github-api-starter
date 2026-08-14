from __future__ import annotations

import os
from pathlib import Path

import pytest

import talend_api_starter.local_project as local_project
from talend_api_starter.errors import BudgetExceeded, ValidationError
from talend_api_starter.synthetic import SYNTHETIC_ITEM, SYNTHETIC_PROPERTIES
from talend_api_starter.xmlsafe import inventory_talend_jobs


def _write_pair(root: Path, prefix: str = "process/demo") -> None:
    destination = root / prefix
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "SyntheticCustomers_0.1.properties").write_bytes(
        SYNTHETIC_PROPERTIES
    )
    (destination / "SyntheticCustomers_0.1.item").write_bytes(SYNTHETIC_ITEM)


def _symlink_or_skip(target: Path, link: Path, *, directory: bool) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks are unavailable in this test environment")


def test_default_process_scan_returns_inventory_compatible_relative_paths(
    tmp_path: Path,
) -> None:
    _write_pair(tmp_path)
    ordinary = tmp_path / "process" / "application.properties"
    ordinary.write_text("password=must-not-be-collected", encoding="utf-8")
    (tmp_path / "process" / "notes.txt").write_text("ignored", encoding="utf-8")

    files = local_project.read_local_job_files(tmp_path)

    assert sorted(files) == [
        "process/demo/SyntheticCustomers_0.1.item",
        "process/demo/SyntheticCustomers_0.1.properties",
    ]
    assert all(not Path(path).is_absolute() for path in files)
    assert b"must-not-be-collected" not in b"".join(files.values())
    inventory = inventory_talend_jobs(files)
    assert inventory.warnings == ()
    assert [job.label for job in inventory.jobs] == ["SyntheticCustomers"]


def test_explicit_prefix_is_safe_portable_and_still_root_relative(
    tmp_path: Path,
) -> None:
    _write_pair(tmp_path, "jobs/team")

    files = local_project.read_local_job_files(
        tmp_path,
        path_prefix=r"jobs\team",
    )

    assert sorted(files) == [
        "jobs/team/SyntheticCustomers_0.1.item",
        "jobs/team/SyntheticCustomers_0.1.properties",
    ]


@pytest.mark.parametrize(
    "path_prefix",
    ["", ".", "..", "../process", "/process", "process/", "process//demo", "C:/x"],
)
def test_unsafe_path_prefixes_are_rejected(
    tmp_path: Path,
    path_prefix: str,
) -> None:
    with pytest.raises(ValidationError, match="^invalid_local_path_prefix$"):
        local_project.read_local_job_files(tmp_path, path_prefix=path_prefix)


def test_root_and_prefix_must_be_exact_existing_directories(tmp_path: Path) -> None:
    root_file = tmp_path / "root.txt"
    root_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValidationError, match="^local_root_not_directory$"):
        local_project.read_local_job_files(root_file)

    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    (parent / "process").mkdir()
    with pytest.raises(
        ValidationError,
        match="^local_path_prefix_not_directory$",
    ):
        local_project.read_local_job_files(child)


def test_root_and_prefix_symlinks_are_rejected(tmp_path: Path) -> None:
    real_root = tmp_path / "real-root"
    (real_root / "process").mkdir(parents=True)
    root_link = tmp_path / "root-link"
    _symlink_or_skip(real_root, root_link, directory=True)
    with pytest.raises(ValidationError, match="^local_root_boundary_rejected$"):
        local_project.read_local_job_files(root_link)

    second_root = tmp_path / "second-root"
    second_root.mkdir()
    prefix_link = second_root / "process"
    _symlink_or_skip(real_root / "process", prefix_link, directory=True)
    with pytest.raises(
        ValidationError,
        match="^local_path_prefix_boundary_rejected$",
    ):
        local_project.read_local_job_files(second_root)


def test_nested_repositories_and_symlink_entries_are_not_read(tmp_path: Path) -> None:
    _write_pair(tmp_path, "process/accepted")
    _write_pair(tmp_path, "process/nested-repository")
    (tmp_path / "process" / "nested-repository" / ".git").write_text(
        "gitdir: elsewhere",
        encoding="utf-8",
    )

    outside = tmp_path / "outside"
    _write_pair(outside, "escaped")
    linked_directory = tmp_path / "process" / "linked-directory"
    _symlink_or_skip(outside / "escaped", linked_directory, directory=True)
    linked_file = tmp_path / "process" / "linked.item"
    _symlink_or_skip(
        outside / "escaped" / "SyntheticCustomers_0.1.item",
        linked_file,
        directory=False,
    )

    files = local_project.read_local_job_files(tmp_path)

    assert sorted(files) == [
        "process/accepted/SyntheticCustomers_0.1.item",
        "process/accepted/SyntheticCustomers_0.1.properties",
    ]


def test_large_ordinary_properties_file_is_ignored_before_xml_byte_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = tmp_path / "process"
    process.mkdir()
    (process / "ordinary.properties").write_bytes(b"x" * 200)
    monkeypatch.setattr(local_project, "MAX_LOCAL_FILE_BYTES", 32)

    assert local_project.read_local_job_files(tmp_path) == {}


@pytest.mark.parametrize(
    ("constant", "expected"),
    [
        ("MAX_LOCAL_DIRECTORIES", "local_directory_budget_exceeded"),
        ("MAX_LOCAL_FILES_SCANNED", "local_file_budget_exceeded"),
    ],
)
def test_walk_budgets_fail_closed_without_exposing_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    constant: str,
    expected: str,
) -> None:
    process = tmp_path / "process"
    process.mkdir()
    (process / "ordinary.txt").write_text("ignored", encoding="utf-8")
    monkeypatch.setattr(local_project, constant, 0)

    with pytest.raises(BudgetExceeded) as caught:
        local_project.read_local_job_files(tmp_path)

    assert str(caught.value) == expected
    assert str(tmp_path) not in str(caught.value)


@pytest.mark.parametrize(
    ("constant", "expected"),
    [
        ("MAX_LOCAL_MATCHES", "local_match_budget_exceeded"),
        ("MAX_LOCAL_TOTAL_BYTES", "local_total_byte_budget_exceeded"),
    ],
)
def test_collection_budgets_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    constant: str,
    expected: str,
) -> None:
    _write_pair(tmp_path)
    monkeypatch.setattr(local_project, constant, 0)

    with pytest.raises(BudgetExceeded, match=f"^{expected}$"):
        local_project.read_local_job_files(tmp_path)


def test_per_file_byte_budget_is_enforced_for_talend_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pair(tmp_path)
    monkeypatch.setattr(local_project, "MAX_LOCAL_FILE_BYTES", 32)

    with pytest.raises(
        BudgetExceeded,
        match="^local_file_byte_budget_exceeded$",
    ):
        local_project.read_local_job_files(tmp_path)


def test_simulated_reparse_prefix_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = tmp_path / "process"
    process.mkdir()
    process_identity = (process.lstat().st_dev, process.lstat().st_ino)
    original = local_project._has_reparse_attribute

    def simulated_reparse(file_stat: os.stat_result) -> bool:
        identity = (file_stat.st_dev, file_stat.st_ino)
        return identity == process_identity or original(file_stat)

    monkeypatch.setattr(
        local_project,
        "_has_reparse_attribute",
        simulated_reparse,
    )

    with pytest.raises(
        ValidationError,
        match="^local_path_prefix_boundary_rejected$",
    ):
        local_project.read_local_job_files(tmp_path)
