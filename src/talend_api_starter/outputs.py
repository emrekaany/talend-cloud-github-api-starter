"""Explicit private/local and publication-oriented output contracts."""

from __future__ import annotations

import json
import os
import re
import secrets
import stat
from collections.abc import Iterable, Mapping
from contextlib import suppress
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .errors import ValidationError
from .github import GitHubSnapshot
from .xmlsafe import InventoryResult, JobDescriptor

SCHEMA_VERSION = "2.0"
REDACTED = "[REDACTED]"
_SENSITIVE_KEY_PARTS = (
    "authorization",
    "credential",
    "password",
    "privatekey",
    "secret",
    "token",
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")

_RUN_STATUSES = frozenset(
    {
        "dispatching",
        "deploy_failed",
        "executing",
        "execution_rejected",
        "execution_successful",
        "execution_failed",
        "terminated",
        "terminated_timeout",
        "terminated_shutdown",
    }
)
_EXECUTION_STATUSES = frozenset(
    {
        "EXECUTION_EVENT_RECEIVED",
        "DISPATCHING_FLOW",
        "STARTING_FLOW_EXECUTION",
        "STOPPING_FLOW_EXECUTION",
        "EXECUTION_TERMINATED",
        "EXECUTION_TERMINATED_TIMEOUT",
        "DEPLOY_FAILED",
        "EXECUTION_FAILED",
        "EXECUTION_REJECTED",
        "EXECUTION_SUCCESS",
        "EXECUTION_TERMINATED_SHUTDOWN",
    }
)
_EXECUTION_TYPES = frozenset({"MANUAL", "SCHEDULED", "WEBHOOK", "PLAN"})
_EXECUTION_DESTINATIONS = frozenset(
    {
        "CLOUD",
        "CLOUD_EXCLUSIVE",
        "REMOTE_ENGINE",
        "REMOTE_ENGINE_CLUSTER",
        "ELASTIC_ENGINE",
        "PIPELINE_ENGINE",
    }
)


@dataclass(frozen=True, slots=True)
class OutputPaths:
    local_view: Path
    share_safe: Path


def _normalized_key(key: str) -> str:
    return "".join(character for character in key.lower() if character.isalnum())


def _redact_string(value: str, secrets: Iterable[str]) -> str:
    result = _BEARER_RE.sub(f"Bearer {REDACTED}", value)
    for secret in secrets:
        result = result.replace(secret, REDACTED)
    return result


def _safe_key_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return str(value)
    return REDACTED


def redact_payload(value: Any, *, secrets: Iterable[str] = ()) -> Any:
    """Recursively redact by key and by exact in-process secret value."""

    normalized_secrets = tuple(
        secret for secret in secrets if isinstance(secret, str) and secret
    )
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, child in value.items():
            raw_key_text = _safe_key_text(raw_key)
            key = _redact_string(raw_key_text, normalized_secrets)
            normalized = _normalized_key(raw_key_text)
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                result[key] = REDACTED
            else:
                result[key] = redact_payload(child, secrets=normalized_secrets)
        return result
    if isinstance(value, list):
        return [redact_payload(child, secrets=normalized_secrets) for child in value]
    if isinstance(value, tuple):
        return [redact_payload(child, secrets=normalized_secrets) for child in value]
    if isinstance(value, str):
        return _redact_string(value, normalized_secrets)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return REDACTED


def _job_local(job: JobDescriptor) -> dict[str, Any]:
    return {
        "label": job.label,
        "version": job.version,
        "status": job.status,
        "properties_path": job.properties_path,
        "item_path": job.item_path,
        "components": [asdict(component) for component in job.components],
    }


def _count_allowlisted(
    values: Iterable[Any], allowlist: frozenset[str]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if isinstance(value, str) and value:
            bucket = value if value in allowlist else "other"
            counts[bucket] = counts.get(bucket, 0) + 1
    return dict(sorted(counts.items()))


def _job_aggregates(jobs: Iterable[JobDescriptor]) -> dict[str, Any]:
    job_list = list(jobs)
    return {
        "job_count": len(job_list),
        "component_count": sum(len(job.components) for job in job_list),
    }


def github_job_outputs(
    snapshot: GitHubSnapshot,
    inventory: InventoryResult,
) -> tuple[dict[str, Any], dict[str, Any]]:
    common_source = {
        "provider": "github_public_api",
        "owner": snapshot.owner,
        "repository": snapshot.repository,
        "ref": snapshot.ref,
        "commit_sha": snapshot.commit_sha,
        "root_tree_sha": snapshot.root_tree_sha,
        "path_prefix": snapshot.path_prefix,
    }
    local_view = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "local_view",
        "source": common_source,
        "job_count": len(inventory.jobs),
        "jobs": [_job_local(job) for job in inventory.jobs],
        "warnings": list(inventory.warnings),
    }
    share_safe = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "share_safe",
        "source": {"provider": "github_public_api"},
        "aggregates": _job_aggregates(inventory.jobs),
        "warning_count": len(inventory.warnings),
    }
    return local_view, share_safe


def local_job_outputs(
    *,
    path_prefix: str,
    inventory: InventoryResult,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build local-only details and an identity-free aggregate projection."""

    local_view = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "local_view",
        "source": {
            "provider": "local_talend_project",
            "path_prefix": path_prefix,
        },
        "job_count": len(inventory.jobs),
        "jobs": [_job_local(job) for job in inventory.jobs],
        "warnings": list(inventory.warnings),
    }
    share_safe = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "share_safe",
        "source": {"provider": "local_talend_project"},
        "aggregates": _job_aggregates(inventory.jobs),
        "warning_count": len(inventory.warnings),
    }
    return local_view, share_safe


def synthetic_demo_outputs(
    inventory: InventoryResult,
    talend_metadata: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    local_view = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "local_view",
        "source": {"provider": "offline_synthetic_fixture"},
        "job_count": len(inventory.jobs),
        "jobs": [_job_local(job) for job in inventory.jobs],
        "warnings": list(inventory.warnings),
        "talend_metadata": redact_payload(talend_metadata),
    }
    share_safe = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "share_safe",
        "source": {"provider": "offline_synthetic_fixture"},
        "studio_aggregates": _job_aggregates(inventory.jobs),
        "talend_aggregates": {
            resource: _talend_aggregates(resource, payload)
            for resource, payload in talend_metadata.items()
            if resource in {"workspaces", "tasks", "runs"}
        },
        "warning_count": len(inventory.warnings),
    }
    return local_view, share_safe


def _records(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("items", "data", "results", "content", "executions"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, Mapping)]
    return []


def _talend_aggregates(resource: str, payload: Any) -> dict[str, Any]:
    records = _records(payload)
    aggregates: dict[str, Any] = {"record_count": len(records)}
    if resource == "runs":
        aggregates["status_counts"] = _count_allowlisted(
            (record.get("status") for record in records), _RUN_STATUSES
        )
        aggregates["execution_status_counts"] = _count_allowlisted(
            (record.get("executionStatus") for record in records),
            _EXECUTION_STATUSES,
        )
        aggregates["execution_type_counts"] = _count_allowlisted(
            (record.get("executionType") for record in records), _EXECUTION_TYPES
        )
        aggregates["execution_destination_counts"] = _count_allowlisted(
            (record.get("executionDestination") for record in records),
            _EXECUTION_DESTINATIONS,
        )
    return aggregates


def talend_outputs(
    *,
    region: str,
    resource: str,
    payload: Any,
    secrets: Iterable[str] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    if resource not in {"workspaces", "tasks", "runs"}:
        raise ValueError("Unsupported Talend API resource")
    local_view = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "local_view",
        "source": {
            "provider": "talend_api",
            "region": region,
            "resource": resource,
        },
        "response": redact_payload(payload, secrets=secrets),
    }
    share_safe = {
        "schema_version": SCHEMA_VERSION,
        "output_class": "share_safe",
        "source": {
            "provider": "talend_api",
            "resource": resource,
        },
        "aggregates": _talend_aggregates(resource, payload),
    }
    return local_view, share_safe


def _write_json(path: Path, payload: Mapping[str, Any], mode: int) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        if os.name != "nt":
            os.fchmod(descriptor, mode)
        # Windows applies the destination directory's ACL. POSIX chmod modes
        # neither model nor strengthen that ACL, so do not pretend they do.
        encoded = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise


def _is_windows_junction(directory_stat: object) -> bool:
    junction_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", None)
    reparse_tag = getattr(directory_stat, "st_reparse_tag", None)
    return junction_tag is not None and reparse_tag == junction_tag


def _prepare_output_directory(destination: Path) -> None:
    with suppress(FileExistsError):
        destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    directory_stat = destination.lstat()
    if (
        stat.S_ISLNK(directory_stat.st_mode)
        or _is_windows_junction(directory_stat)
        or not stat.S_ISDIR(directory_stat.st_mode)
    ):
        raise ValidationError("Output destination must be a real directory")
    if os.name != "nt":
        parent_stat = destination.parent.resolve(strict=True).stat()
        parent_is_writable = bool(parent_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH))
        parent_is_sticky = bool(parent_stat.st_mode & stat.S_ISVTX)
        if parent_is_writable and not parent_is_sticky:
            raise ValidationError("Output parent directory is not trusted")
        if directory_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ValidationError("Output directory must not be group/world writable")
        getuid = getattr(os, "getuid", None)
        if getuid is not None and directory_stat.st_uid != getuid():
            raise ValidationError("Output directory must be owned by the current user")


def write_output_bundle(
    destination: Path,
    local_view: Mapping[str, Any],
    share_safe: Mapping[str, Any],
) -> OutputPaths:
    _prepare_output_directory(destination)
    local_path = destination / "local_view.json"
    share_path = destination / "share_safe.json"
    _write_json(local_path, local_view, 0o600)
    _write_json(share_path, share_safe, 0o644)
    return OutputPaths(local_path, share_path)
