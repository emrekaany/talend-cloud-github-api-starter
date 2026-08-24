"""Strict, GET-only client for a small Qlik Talend API inventory surface."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

from ._version import USER_AGENT
from .errors import ApiError, ConfigurationError, ValidationError
from .http import DEFAULT_TIMEOUT, BoundedJsonClient

# This literal is the environment-variable name, never a credential value.
TALEND_TOKEN_ENV = "TALEND_TOKEN"  # nosec B105
TALEND_BASE_URL_ENV = "TALEND_BASE_URL"
TALEND_API_VERSION = "2021-03"

# Qlik currently hosts the documented Talend Orchestration and Processing APIs
# on regional cloud.talend.com hosts. This protocol constraint is deliberately
# separate from the product's public name, "Talend API + GitHub API CLI".
_OFFICIAL_HOST_RE = re.compile(
    r"^api\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.cloud\.talend\.com$"
)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ENVIRONMENT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,99}$")
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
_ALLOWED_ENDPOINTS = frozenset(
    {
        "/orchestration/workspaces",
        "/orchestration/executables/tasks",
        "/processing/executables/tasks/executions",
    }
)


def validate_official_talend_base_url(base_url: str) -> str:
    """Allow only exact HTTPS API hosts documented by Qlik Talend."""

    try:
        parsed = urlsplit(base_url)
    except ValueError:
        raise ValidationError("Talend base URL is invalid") from None
    if parsed.scheme != "https":
        raise ValidationError("Talend base URL must use HTTPS")
    if parsed.username or parsed.password:
        raise ValidationError("Talend base URL must not contain credentials")
    try:
        explicit_port = parsed.port
    except ValueError:
        raise ValidationError("Talend base URL contains an invalid port") from None
    if explicit_port is not None:
        raise ValidationError("Talend base URL must not specify a port")
    hostname = (parsed.hostname or "").lower()
    if not _OFFICIAL_HOST_RE.fullmatch(hostname):
        raise ValidationError("Talend base URL host is not an official API host")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValidationError(
            "Talend base URL must not contain a path, query, or fragment"
        )
    return f"https://{hostname}"


def _optional_identifier(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValidationError(f"Invalid {field}")
    return value


def _bounded_page(limit: int, offset: int) -> tuple[int, int]:
    if not 1 <= limit <= 100:
        raise ValidationError("limit must be between 1 and 100")
    if not 0 <= offset <= 1_000:
        raise ValidationError("offset must be between 0 and 1000")
    return limit, offset


def _validated_record_list(payload: Any, code: str) -> list[Mapping[str, Any]]:
    if not isinstance(payload, list) or any(
        not isinstance(record, Mapping) for record in payload
    ):
        raise ApiError("talend_api", 200, code)
    return payload


def _validated_page(payload: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ApiError("talend_api", 200, code)
    items = payload.get("items")
    if not isinstance(items, list) or any(
        not isinstance(record, Mapping) for record in items
    ):
        raise ApiError("talend_api", 200, code)
    return payload


class TalendApiClient:
    """Read-only client for documented Talend Orchestration/Processing APIs.

    The token has no constructor or method parameter. It is read only from
    ``TALEND_TOKEN`` and is never placed in an exception or output object.
    """

    def __init__(
        self,
        base_url: str,
        *,
        max_requests: int = 8,
        max_response_bytes: int = 2_000_000,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        base_url = validate_official_talend_base_url(base_url)
        token = os.environ.get(TALEND_TOKEN_ENV, "").strip()
        if not token:
            raise ConfigurationError(
                f"Set {TALEND_TOKEN_ENV} in the process environment"
            )
        try:
            token.encode("ascii")
        except UnicodeEncodeError:
            raise ConfigurationError(
                f"{TALEND_TOKEN_ENV} contains invalid characters"
            ) from None
        if any(ord(character) < 32 or ord(character) == 127 for character in token):
            raise ConfigurationError(f"{TALEND_TOKEN_ENV} contains invalid characters")
        self.base_url = base_url
        self.region = base_url.removeprefix("https://api.").removesuffix(
            ".cloud.talend.com"
        )
        self._redaction_secrets = (token,)
        self._http = BoundedJsonClient(
            provider="talend_api",
            base_url=base_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "talend-version": TALEND_API_VERSION,
                "User-Agent": USER_AGENT,
            },
            max_requests=max_requests,
            max_response_bytes=max_response_bytes,
            allowed_paths=_ALLOWED_ENDPOINTS,
            timeout=timeout,
            transport=transport,
        )

    @classmethod
    def from_env(cls, **kwargs: Any) -> TalendApiClient:
        base_url = os.environ.get(TALEND_BASE_URL_ENV, "").strip()
        if not base_url:
            raise ConfigurationError(
                f"Set {TALEND_BASE_URL_ENV} in the process environment"
            )
        return cls(base_url, **kwargs)

    @property
    def request_count(self) -> int:
        return self._http.request_count

    @property
    def redaction_secrets(self) -> tuple[str, ...]:
        """Return the exact normalized credential already held by this client."""

        return self._redaction_secrets

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> TalendApiClient:
        return self

    def __exit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        self._http.__exit__(exception_type, exception, traceback)

    def list_workspaces(
        self,
        *,
        environment_name: str | None = None,
    ) -> Any:
        params: dict[str, str | int] = {}
        if environment_name is not None:
            environment_name = environment_name.strip()
            if not _ENVIRONMENT_NAME_RE.fullmatch(environment_name):
                raise ValidationError("Invalid environment name")
            params["query"] = f"environment.name=={environment_name}"
        payload = self._http.get_json("/orchestration/workspaces", params=params)
        return _validated_record_list(payload, "invalid_workspaces_response")

    def list_tasks(
        self,
        *,
        workspace_id: str | None = None,
        artifact_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Any:
        limit, offset = _bounded_page(limit, offset)
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        workspace_id = _optional_identifier(workspace_id, "workspace ID")
        artifact_id = _optional_identifier(artifact_id, "artifact ID")
        if workspace_id:
            params["workspaceId"] = workspace_id
        if artifact_id:
            params["artifactId"] = artifact_id
        payload = self._http.get_json("/orchestration/executables/tasks", params=params)
        return _validated_page(payload, "invalid_tasks_response")

    def list_runs(
        self,
        *,
        workspace_id: str | None = None,
        status: str | None = None,
        last_days: int = 7,
        limit: int = 100,
        offset: int = 0,
    ) -> Any:
        limit, offset = _bounded_page(limit, offset)
        if not 1 <= last_days <= 10:
            raise ValidationError("last_days must be between 1 and 10")
        params: dict[str, str | int] = {
            "lastDays": last_days,
            "limit": limit,
            "offset": offset,
        }
        workspace_id = _optional_identifier(workspace_id, "workspace ID")
        if workspace_id:
            params["workspaceId"] = workspace_id
        if status is not None:
            status = status.strip().lower()
            if status not in _RUN_STATUSES:
                raise ValidationError("Invalid run status")
            params["status"] = status
        payload = self._http.get_json(
            "/processing/executables/tasks/executions", params=params
        )
        return _validated_page(payload, "invalid_runs_response")
