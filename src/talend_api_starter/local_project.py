"""Bounded, read-only collection of local Talend Studio job artifacts.

The collector never invokes Git or a network client.  It returns repository-relative
paths and in-memory bytes for the strict XML inventory parser; file contents and
absolute local paths are deliberately absent from user-facing errors.
"""

from __future__ import annotations

import os
import stat
from contextlib import suppress
from pathlib import Path

from .errors import BudgetExceeded, ValidationError

MAX_LOCAL_DIRECTORIES = 20_000
MAX_LOCAL_FILES_SCANNED = 100_000
MAX_LOCAL_MATCHES = 2_000
MAX_LOCAL_FILE_BYTES = 1_000_000
MAX_LOCAL_TOTAL_BYTES = 64_000_000

_MAX_PREFIX_LENGTH = 1_024
_MARKER_PROBE_BYTES = 64 * 1_024
_TALEND_PROPERTIES_MARKER = b"http://www.talend.org/properties"
_REPARSE_POINT_FLAG = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _has_reparse_attribute(file_stat: os.stat_result) -> bool:
    attributes = getattr(file_stat, "st_file_attributes", 0)
    return bool(attributes & _REPARSE_POINT_FLAG)


def _is_link_or_reparse(file_stat: os.stat_result) -> bool:
    return stat.S_ISLNK(file_stat.st_mode) or _has_reparse_attribute(file_stat)


def _safe_lstat(path: Path, error_code: str) -> os.stat_result:
    try:
        return path.lstat()
    except (OSError, ValueError):
        raise ValidationError(error_code) from None


def _validate_root(root: str | os.PathLike[str]) -> Path:
    raw_root = os.fspath(root)
    if not raw_root or "\x00" in raw_root:
        raise ValidationError("local_root_required")
    root_path = Path(raw_root)
    root_stat = _safe_lstat(root_path, "local_root_not_directory")
    if _is_link_or_reparse(root_stat):
        raise ValidationError("local_root_boundary_rejected")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValidationError("local_root_not_directory")
    try:
        resolved = root_path.resolve(strict=True)
    except (OSError, RuntimeError):
        raise ValidationError("local_root_not_directory") from None
    resolved_stat = _safe_lstat(resolved, "local_root_not_directory")
    if _is_link_or_reparse(resolved_stat) or not stat.S_ISDIR(resolved_stat.st_mode):
        raise ValidationError("local_root_boundary_rejected")
    return resolved


def _safe_prefix_parts(path_prefix: str) -> tuple[str, ...]:
    if not isinstance(path_prefix, str):
        raise ValidationError("invalid_local_path_prefix")
    try:
        path_prefix.encode("utf-8")
    except UnicodeEncodeError:
        raise ValidationError("invalid_local_path_prefix") from None
    portable = path_prefix.replace("\\", "/")
    if (
        not portable
        or len(portable) > _MAX_PREFIX_LENGTH
        or portable.startswith("/")
        or portable.endswith("/")
        or "\x00" in portable
    ):
        raise ValidationError("invalid_local_path_prefix")
    parts = tuple(portable.split("/"))
    if any(
        not part
        or part in {".", ".."}
        or ":" in part
        or any(ord(character) < 32 or ord(character) == 127 for character in part)
        for part in parts
    ):
        raise ValidationError("invalid_local_path_prefix")
    return parts


def _validate_scan_root(root: Path, path_prefix: str) -> Path:
    current = root
    for part in _safe_prefix_parts(path_prefix):
        current /= part
        current_stat = _safe_lstat(current, "local_path_prefix_not_directory")
        if _is_link_or_reparse(current_stat) or os.path.ismount(current):
            raise ValidationError("local_path_prefix_boundary_rejected")
        if not stat.S_ISDIR(current_stat.st_mode):
            raise ValidationError("local_path_prefix_not_directory")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise ValidationError("local_path_prefix_boundary_rejected") from None
    return resolved


def _walk_error(_error: OSError) -> None:
    raise ValidationError("local_project_walk_failed")


def _safe_directory_for_descent(path: Path, root: Path) -> bool:
    try:
        file_stat = path.lstat()
        if (
            _is_link_or_reparse(file_stat)
            or not stat.S_ISDIR(file_stat.st_mode)
            or os.path.ismount(path)
        ):
            return False
        path.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _safe_repository_relative_path(path: Path, repository: Path) -> str:
    try:
        relative_path = path.relative_to(repository).as_posix()
        relative_path.encode("utf-8")
    except (UnicodeEncodeError, ValueError):
        raise ValidationError("local_project_path_rejected") from None
    if any(ord(character) < 32 or ord(character) == 127 for character in relative_path):
        raise ValidationError("local_project_path_rejected")
    return relative_path


def _open_read_only(path: Path) -> tuple[int, os.stat_result, os.stat_result]:
    before = _safe_lstat(path, "local_project_file_read_failed")
    if _is_link_or_reparse(before) or not stat.S_ISREG(before.st_mode):
        raise ValidationError("local_project_boundary_changed")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        raise ValidationError("local_project_file_read_failed") from None
    try:
        after = os.fstat(descriptor)
    except OSError:
        os.close(descriptor)
        raise ValidationError("local_project_file_read_failed") from None
    if (
        _is_link_or_reparse(after)
        or not stat.S_ISREG(after.st_mode)
        or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
    ):
        os.close(descriptor)
        raise ValidationError("local_project_boundary_changed")
    return descriptor, before, after


def _read_candidate(path: Path, *, properties_file: bool) -> bytes | None:
    descriptor, _before, opened_stat = _open_read_only(path)
    try:
        try:
            stream = os.fdopen(descriptor, "rb")
        except BaseException:
            with suppress(OSError):
                os.close(descriptor)
            raise
        with stream:
            if properties_file:
                probe = stream.read(_MARKER_PROBE_BYTES)
                if _TALEND_PROPERTIES_MARKER not in probe:
                    return None
                stream.seek(0)
            if opened_stat.st_size > MAX_LOCAL_FILE_BYTES:
                raise BudgetExceeded("local_file_byte_budget_exceeded")
            content = stream.read(MAX_LOCAL_FILE_BYTES + 1)
    except BudgetExceeded:
        raise
    except OSError:
        raise ValidationError("local_project_file_read_failed") from None
    if len(content) > MAX_LOCAL_FILE_BYTES:
        raise BudgetExceeded("local_file_byte_budget_exceeded")
    return content


def read_local_job_files(
    root: str | os.PathLike[str],
    *,
    path_prefix: str = "process",
) -> dict[str, bytes]:
    """Read Talend ``.properties``/``.item`` files below one exact directory.

    ``path_prefix`` is mandatory-safe and repository-relative; callers may omit it
    to use Talend Studio's conventional ``process`` directory.  The returned keys
    remain relative to ``root`` so they can be passed directly to
    :func:`talend_api_starter.xmlsafe.inventory_talend_jobs`.
    """

    repository = _validate_root(root)
    scan_root = _validate_scan_root(repository, path_prefix)
    collected: dict[str, bytes] = {}
    directories_seen = 0
    files_seen = 0
    matched_bytes = 0

    for current, directory_names, file_names in os.walk(
        scan_root,
        topdown=True,
        onerror=_walk_error,
        followlinks=False,
    ):
        directories_seen += 1
        if directories_seen > MAX_LOCAL_DIRECTORIES:
            raise BudgetExceeded("local_directory_budget_exceeded")

        current_path = Path(current)
        has_git_marker = ".git" in directory_names or ".git" in file_names
        if current_path != scan_root and has_git_marker:
            directory_names[:] = []
            continue

        directory_names[:] = sorted(
            directory_name
            for directory_name in directory_names
            if directory_name != ".git"
            and _safe_directory_for_descent(
                current_path / directory_name,
                repository,
            )
        )
        file_names.sort()
        files_seen += len(file_names)
        if files_seen > MAX_LOCAL_FILES_SCANNED:
            raise BudgetExceeded("local_file_budget_exceeded")

        for file_name in file_names:
            properties_file = file_name.endswith(".properties")
            if not properties_file and not file_name.endswith(".item"):
                continue
            path = current_path / file_name
            relative_path = _safe_repository_relative_path(path, repository)
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(repository)
            except (OSError, RuntimeError, ValueError):
                raise ValidationError("local_project_boundary_changed") from None
            file_stat = _safe_lstat(path, "local_project_file_read_failed")
            if _is_link_or_reparse(file_stat) or not stat.S_ISREG(file_stat.st_mode):
                continue

            content = _read_candidate(path, properties_file=properties_file)
            if content is None:
                continue
            if len(collected) >= MAX_LOCAL_MATCHES:
                raise BudgetExceeded("local_match_budget_exceeded")
            matched_bytes += len(content)
            if matched_bytes > MAX_LOCAL_TOTAL_BYTES:
                raise BudgetExceeded("local_total_byte_budget_exceeded")
            collected[relative_path] = content

    return collected
