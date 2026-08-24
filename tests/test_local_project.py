from __future__ import annotations

import os
import stat
from pathlib import Path
from types import SimpleNamespace

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
    [
        "",
        ".",
        "..",
        "../process",
        "/process",
        "process/",
        "process//demo",
        "C:/x",
        "process/invalid_\udcff",
    ],
)
def test_unsafe_path_prefixes_are_rejected(
    tmp_path: Path,
    path_prefix: str,
) -> None:
    with pytest.raises(ValidationError, match="^invalid_local_path_prefix$"):
        local_project.read_local_job_files(tmp_path, path_prefix=path_prefix)


@pytest.mark.parametrize("root", ["", "\x00"])
def test_empty_or_nul_root_is_rejected(root: str) -> None:
    with pytest.raises(ValidationError, match="^local_root_required$"):
        local_project.read_local_job_files(root)


def test_non_string_prefix_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="^invalid_local_path_prefix$"):
        local_project.read_local_job_files(tmp_path, path_prefix=object())  # type: ignore[arg-type]


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

    prefix_file_root = tmp_path / "prefix-file-root"
    prefix_file_root.mkdir()
    (prefix_file_root / "process").write_text("not a directory", encoding="utf-8")
    with pytest.raises(
        ValidationError,
        match="^local_path_prefix_not_directory$",
    ):
        local_project.read_local_job_files(prefix_file_root)


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


def test_root_resolution_failure_is_redacted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_resolve = Path.resolve

    def fail_root_resolution(self: Path, strict: bool = False) -> Path:
        if self == tmp_path:
            raise OSError("synthetic root resolution failure")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", fail_root_resolution)
    with pytest.raises(ValidationError, match="^local_root_not_directory$") as caught:
        local_project.read_local_job_files(tmp_path)
    assert str(tmp_path) not in str(caught.value)


def test_root_type_change_after_resolution_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_safe_lstat = local_project._safe_lstat
    root_checks = 0

    def changed_root_stat(path: Path, error_code: str) -> os.stat_result:
        nonlocal root_checks
        result = original_safe_lstat(path, error_code)
        if path == tmp_path:
            root_checks += 1
            if root_checks == 2:
                return SimpleNamespace(  # type: ignore[return-value]
                    st_mode=stat.S_IFREG,
                    st_file_attributes=0,
                )
        return result

    monkeypatch.setattr(local_project, "_safe_lstat", changed_root_stat)
    with pytest.raises(ValidationError, match="^local_root_boundary_rejected$"):
        local_project.read_local_job_files(tmp_path)


def test_prefix_escape_during_resolution_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = tmp_path / "process"
    process.mkdir()
    original_resolve = Path.resolve

    def escape_prefix(self: Path, strict: bool = False) -> Path:
        if self == process:
            return tmp_path.parent
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", escape_prefix)
    with pytest.raises(
        ValidationError,
        match="^local_path_prefix_boundary_rejected$",
    ):
        local_project.read_local_job_files(tmp_path)


def test_walk_error_is_converted_to_redacted_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "process").mkdir()

    def failing_walk(*_args: object, **kwargs: object) -> tuple[()]:
        onerror = kwargs["onerror"]
        assert callable(onerror)
        onerror(OSError("synthetic walk failure"))
        return ()

    monkeypatch.setattr(local_project.os, "walk", failing_walk)
    with pytest.raises(ValidationError, match="^local_project_walk_failed$") as caught:
        local_project.read_local_job_files(tmp_path)
    assert str(tmp_path) not in str(caught.value)


def test_directory_disappearing_during_descent_is_skipped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = tmp_path / "process"
    process.mkdir()

    def changing_walk(*_args: object, **_kwargs: object) -> object:
        return iter([(str(process), ["disappeared"], [])])

    monkeypatch.setattr(local_project.os, "walk", changing_walk)
    assert local_project.read_local_job_files(tmp_path) == {}


def test_file_type_swap_before_open_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pair(tmp_path)
    target = tmp_path / "process" / "demo" / "SyntheticCustomers_0.1.item"
    original_safe_lstat = local_project._safe_lstat
    target_checks = 0

    def swapped_stat(path: Path, error_code: str) -> os.stat_result:
        nonlocal target_checks
        result = original_safe_lstat(path, error_code)
        if path == target:
            target_checks += 1
            if target_checks == 2:
                return SimpleNamespace(  # type: ignore[return-value]
                    st_mode=stat.S_IFDIR,
                    st_file_attributes=0,
                )
        return result

    monkeypatch.setattr(local_project, "_safe_lstat", swapped_stat)
    with pytest.raises(ValidationError, match="^local_project_boundary_changed$"):
        local_project.read_local_job_files(tmp_path)


def test_open_failure_is_converted_to_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"synthetic")
    original_open = os.open

    def fail_target_open(path: os.PathLike[str] | str, flags: int) -> int:
        if Path(path) == target:
            raise OSError("synthetic open failure")
        return original_open(path, flags)

    monkeypatch.setattr(local_project.os, "open", fail_target_open)
    with pytest.raises(ValidationError, match="^local_project_file_read_failed$"):
        local_project._open_read_only(target)


def test_fstat_failure_closes_the_open_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"synthetic")
    original_open = os.open
    original_fstat = os.fstat
    target_descriptors: list[int] = []

    def track_target_open(path: os.PathLike[str] | str, flags: int) -> int:
        descriptor = original_open(path, flags)
        if Path(path) == target:
            target_descriptors.append(descriptor)
        return descriptor

    def fail_target_fstat(descriptor: int) -> os.stat_result:
        if descriptor in target_descriptors:
            raise OSError("synthetic fstat failure")
        return original_fstat(descriptor)

    monkeypatch.setattr(local_project.os, "open", track_target_open)
    monkeypatch.setattr(local_project.os, "fstat", fail_target_fstat)
    with pytest.raises(ValidationError, match="^local_project_file_read_failed$"):
        local_project._open_read_only(target)

    assert len(target_descriptors) == 1
    with pytest.raises(OSError):
        original_fstat(target_descriptors[0])


def test_inode_swap_after_open_is_rejected_and_descriptor_is_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"synthetic")
    original_open = os.open
    original_fstat = os.fstat
    target_descriptors: list[int] = []

    def track_target_open(path: os.PathLike[str] | str, flags: int) -> int:
        descriptor = original_open(path, flags)
        if Path(path) == target:
            target_descriptors.append(descriptor)
        return descriptor

    def report_changed_inode(descriptor: int) -> os.stat_result:
        result = original_fstat(descriptor)
        if descriptor in target_descriptors:
            return SimpleNamespace(  # type: ignore[return-value]
                st_mode=result.st_mode,
                st_dev=result.st_dev,
                st_ino=result.st_ino + 1,
                st_file_attributes=getattr(result, "st_file_attributes", 0),
            )
        return result

    monkeypatch.setattr(local_project.os, "open", track_target_open)
    monkeypatch.setattr(local_project.os, "fstat", report_changed_inode)
    with pytest.raises(ValidationError, match="^local_project_boundary_changed$"):
        local_project._open_read_only(target)

    assert len(target_descriptors) == 1
    with pytest.raises(OSError):
        original_fstat(target_descriptors[0])


def test_stream_read_failure_is_converted_to_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"synthetic")

    class FailingStream:
        def __init__(self, descriptor: int) -> None:
            self.descriptor = descriptor

        def __enter__(self) -> FailingStream:
            return self

        def __exit__(self, *_args: object) -> None:
            os.close(self.descriptor)

        def read(self, _size: int) -> bytes:
            raise OSError("synthetic read failure")

    monkeypatch.setattr(
        local_project.os,
        "fdopen",
        lambda descriptor, _mode: FailingStream(descriptor),
    )
    with pytest.raises(ValidationError, match="^local_project_file_read_failed$"):
        local_project._read_candidate(target, properties_file=False)


def test_fdopen_failure_closes_descriptor_and_returns_safe_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"synthetic")
    opened_descriptors: list[int] = []

    def fail_fdopen(descriptor: int, _mode: str) -> None:
        opened_descriptors.append(descriptor)
        raise OSError("synthetic fdopen failure")

    monkeypatch.setattr(local_project.os, "fdopen", fail_fdopen)
    with pytest.raises(ValidationError, match="^local_project_file_read_failed$"):
        local_project._read_candidate(target, properties_file=False)

    assert len(opened_descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(opened_descriptors[0])


def test_file_growth_after_open_still_respects_read_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate.item"
    target.write_bytes(b"four")
    actual_stat = target.stat()

    def stale_open_stat(_path: Path) -> tuple[int, os.stat_result, object]:
        descriptor = os.open(target, os.O_RDONLY)
        return descriptor, actual_stat, SimpleNamespace(st_size=0)

    monkeypatch.setattr(local_project, "MAX_LOCAL_FILE_BYTES", 3)
    monkeypatch.setattr(local_project, "_open_read_only", stale_open_stat)
    with pytest.raises(BudgetExceeded, match="^local_file_byte_budget_exceeded$"):
        local_project._read_candidate(target, properties_file=False)


def test_candidate_resolution_failure_is_treated_as_boundary_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_pair(tmp_path)
    target = tmp_path / "process" / "demo" / "SyntheticCustomers_0.1.item"
    original_resolve = Path.resolve

    def fail_candidate_resolution(self: Path, strict: bool = False) -> Path:
        if self == target:
            raise OSError("synthetic candidate resolution failure")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", fail_candidate_resolution)
    with pytest.raises(ValidationError, match="^local_project_boundary_changed$"):
        local_project.read_local_job_files(tmp_path)


@pytest.mark.parametrize("unsafe_name", ["bad_\udcff.item", "bad\x7f.item"])
def test_collected_paths_require_strict_utf8_without_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsafe_name: str,
) -> None:
    process = tmp_path / "process"
    process.mkdir()

    monkeypatch.setattr(
        local_project.os,
        "walk",
        lambda *_args, **_kwargs: iter([(str(process), [], [unsafe_name])]),
    )

    with pytest.raises(ValidationError, match="^local_project_path_rejected$"):
        local_project.read_local_job_files(tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="Windows paths do not expose raw bytes")
def test_posix_undecodable_artifact_name_fails_closed(tmp_path: Path) -> None:
    process = tmp_path / "process"
    process.mkdir()
    raw_path = os.fsencode(process) + b"/Synthetic_\xff.item"
    try:
        descriptor = os.open(raw_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        pytest.skip("filesystem rejects undecodable byte names")
    try:
        os.write(descriptor, SYNTHETIC_ITEM)
    finally:
        os.close(descriptor)

    with pytest.raises(ValidationError, match="^local_project_path_rejected$"):
        local_project.read_local_job_files(tmp_path)
