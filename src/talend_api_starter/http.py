"""Small bounded HTTP/JSON primitive shared by both read-only clients."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

from .errors import ApiError, BudgetExceeded

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


def _safe_retry_after(headers: Mapping[str, str]) -> int | None:
    raw = headers.get("retry-after", "").strip()
    if raw.isascii() and raw.isdigit():
        return min(int(raw), 86_400)
    return None


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
        self._client.close()

    def __enter__(self) -> BoundedJsonClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_json(
        self,
        path: str,
        *,
        params: Mapping[str, str | int] | None = None,
    ) -> Any:
        parsed_path = urlsplit(path)
        if (
            not path.startswith("/")
            or path.startswith("//")
            or "\\" in path
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.query
            or parsed_path.fragment
            or any(ord(character) < 32 for character in path)
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
                and int(declared) > self.max_response_bytes
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
            raise ApiError(self.provider, None, "network_error") from None
        finally:
            response.close()

        try:
            return json.loads(b"".join(chunks))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(
                self.provider, response.status_code, "invalid_json"
            ) from None
