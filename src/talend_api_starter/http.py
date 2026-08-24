"""Small bounded HTTP/JSON primitive shared by both read-only clients."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from contextlib import suppress
from typing import Any
from urllib.parse import urlsplit

import httpx

from .errors import ApiError, BudgetExceeded

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 50_000


def _normalized_decimal(raw: str) -> str:
    return raw.lstrip("0") or "0"


def _decimal_exceeds(raw: str, limit: int) -> bool:
    normalized = _normalized_decimal(raw)
    limit_text = str(limit)
    return len(normalized) > len(limit_text) or (
        len(normalized) == len(limit_text) and normalized > limit_text
    )


def _safe_retry_after(headers: Mapping[str, str]) -> int | None:
    raw = headers.get("retry-after", "").strip()
    if raw.isascii() and raw.isdigit():
        if _decimal_exceeds(raw, 86_400):
            return 86_400
        return int(_normalized_decimal(raw))
    return None


def _reject_json_constant(_: str) -> None:
    raise ValueError("non-standard JSON constant")


def _validate_json_complexity(provider: str, status_code: int, value: Any) -> None:
    """Reject recursive, non-finite, or non-Unicode JSON before consumers see it."""

    nodes_seen = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        nodes_seen += 1
        if depth > MAX_JSON_DEPTH or nodes_seen > MAX_JSON_NODES:
            raise BudgetExceeded(f"{provider}: json_complexity_budget_exceeded")
        if isinstance(current, dict):
            for key, child in current.items():
                try:
                    key.encode("utf-8")
                except UnicodeEncodeError:
                    raise ApiError(provider, status_code, "invalid_json") from None
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
        elif isinstance(current, str):
            try:
                current.encode("utf-8")
            except UnicodeEncodeError:
                raise ApiError(provider, status_code, "invalid_json") from None
        elif isinstance(current, float) and not math.isfinite(current):
            raise ApiError(provider, status_code, "invalid_json")


def status_error(provider: str, response: httpx.Response) -> ApiError:
    """Map status and safe headers without ever reading the response body."""

    status = response.status_code
    retry_after = _safe_retry_after(response.headers)
    if status == 401:
        code = "authentication_failed"
    elif status == 403 and response.headers.get("x-ratelimit-remaining") == "0":
        code = "rate_limited"
    elif status == 403:
        code = "forbidden"
    elif status == 404:
        code = "not_found"
    elif status == 429:
        code = "rate_limited"
    elif status in (502, 503, 504):
        code = "temporarily_unavailable"
    elif 300 <= status < 400:
        code = "redirect_refused"
    else:
        code = "unexpected_status"
    return ApiError(provider, status, code, retry_after)


class BoundedJsonClient:
    """GET-only JSON transport with redirect, request, and byte limits."""

    def __init__(
        self,
        *,
        provider: str,
        base_url: str,
        headers: Mapping[str, str],
        max_requests: int,
        max_response_bytes: int,
        allowed_paths: frozenset[str] | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if max_requests < 1 or max_response_bytes < 1:
            raise ValueError("HTTP budgets must be positive")
        self.provider = provider
        self.max_requests = max_requests
        self.max_response_bytes = max_response_bytes
        self.request_count = 0
        self.trust_env = False
        self._allowed_paths = allowed_paths
        self._client = httpx.Client(
            base_url=base_url,
            headers=dict(headers),
            timeout=timeout,
            follow_redirects=False,
            trust_env=self.trust_env,
            transport=transport,
        )

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            raise ApiError(self.provider, None, "network_error") from None

    def __enter__(self) -> BoundedJsonClient:
        return self

    def __exit__(self, exception_type: object, *_: object) -> None:
        try:
            self.close()
        except ApiError:
            if exception_type is None:
                raise

    def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> Any:
        try:
            path.encode("utf-8")
            parsed_path = urlsplit(path)
        except (UnicodeEncodeError, ValueError):
            raise ApiError(self.provider, None, "invalid_request_target") from None
        if (
            not path.startswith("/")
            or path.startswith("//")
            or "\\" in path
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.query
            or parsed_path.fragment
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
            or (
                self._allowed_paths is not None
                and parsed_path.path not in self._allowed_paths
            )
        ):
            raise ApiError(self.provider, None, "invalid_request_target")
        if self.request_count >= self.max_requests:
            raise BudgetExceeded(f"{self.provider}: request_budget_exceeded")
        self.request_count += 1
        try:
            request = self._client.build_request("GET", path, params=params)
            response = self._client.send(request, stream=True, follow_redirects=False)
        except httpx.HTTPError:
            raise ApiError(self.provider, None, "network_error") from None

        try:
            if response.status_code != 200:
                raise status_error(self.provider, response)
            content_type = response.headers.get("content-type")
            if content_type:
                media_type = content_type.split(";", 1)[0].strip().lower()
                if media_type != "application/json" and not media_type.endswith(
                    "+json"
                ):
                    raise ApiError(
                        self.provider, response.status_code, "invalid_content_type"
                    )
            declared = response.headers.get("content-length", "")
            if (
                declared.isascii()
                and declared.isdigit()
                and _decimal_exceeds(declared, self.max_response_bytes)
            ):
                raise BudgetExceeded(f"{self.provider}: response_byte_budget_exceeded")
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > self.max_response_bytes:
                    raise BudgetExceeded(
                        f"{self.provider}: response_byte_budget_exceeded"
                    )
                chunks.append(chunk)
        except httpx.HTTPError:
            with suppress(Exception):
                response.close()
            raise ApiError(self.provider, None, "network_error") from None
        except BaseException:
            with suppress(Exception):
                response.close()
            raise
        try:
            response.close()
        except Exception:
            raise ApiError(self.provider, None, "network_error") from None

        try:
            payload = json.loads(
                b"".join(chunks),
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
            raise ApiError(
                self.provider, response.status_code, "invalid_json"
            ) from None
        _validate_json_complexity(self.provider, response.status_code, payload)
        return payload
