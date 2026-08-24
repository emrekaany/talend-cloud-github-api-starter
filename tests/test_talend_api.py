"""Contract and security tests for the GET-only Talend API client."""

from __future__ import annotations

import gzip
import json
from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest

from talend_api_starter.errors import (
    ApiError,
    BudgetExceeded,
    ConfigurationError,
    ValidationError,
)
from talend_api_starter.http import BoundedJsonClient
from talend_api_starter.talend_api import (
    TALEND_API_VERSION,
    TALEND_BASE_URL_ENV,
    TALEND_TOKEN_ENV,
    TalendApiClient,
    validate_official_talend_base_url,
)


@pytest.fixture(autouse=True)
def talend_pat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TALEND_TOKEN_ENV, "talend_pat_super_secret")
    monkeypatch.setenv(TALEND_BASE_URL_ENV, "https://api.eu.cloud.talend.com")


@pytest.mark.parametrize(
    "url",
    [
        "http://api.eu.cloud.talend.com",
        "https://api.eu.cloud.talend.com.evil.example",
        "https://user@api.eu.cloud.talend.com",
        "https://api.eu.cloud.talend.com:443",
        "https://api.eu.cloud.talend.com:8443",
        "https://api.eu.cloud.talend.com:not-a-port",
        "https://[",
        "https://[]",
        "https://api.eu.cloud.talend.com/orchestration",
        "https://api.eu.cloud.talend.com?next=evil",
    ],
)
def test_official_host_validation_rejects_lookalikes(url: str) -> None:
    with pytest.raises(ValidationError):
        validate_official_talend_base_url(url)


def test_pat_is_required_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TALEND_TOKEN_ENV)
    with pytest.raises(ConfigurationError, match=TALEND_TOKEN_ENV):
        TalendApiClient.from_env()


def test_base_url_is_required_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(TALEND_BASE_URL_ENV)
    with pytest.raises(ConfigurationError, match=TALEND_BASE_URL_ENV):
        TalendApiClient.from_env()


@pytest.mark.parametrize(
    "token",
    ["first-line\nsecond-line", "first\tsecond", "first\x7fsecond", "tökén"],
)
def test_token_rejects_non_ascii_and_control_characters(
    monkeypatch: pytest.MonkeyPatch,
    token: str,
) -> None:
    monkeypatch.setenv(TALEND_TOKEN_ENV, token)
    with pytest.raises(ConfigurationError, match="invalid characters"):
        TalendApiClient.from_env()


def test_documented_region_pattern_is_not_a_closed_enum() -> None:
    url = "https://api.ca-central.cloud.talend.com"
    assert validate_official_talend_base_url(url) == url


@pytest.mark.parametrize(
    ("max_requests", "max_response_bytes"),
    [(0, 1), (1, 0)],
)
def test_http_budgets_must_be_positive(
    max_requests: int, max_response_bytes: int
) -> None:
    with pytest.raises(ValueError, match="HTTP budgets must be positive"):
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=max_requests,
            max_response_bytes=max_response_bytes,
        )


@pytest.mark.parametrize("path", ["//[", "/bad\x7fpath", "/bad\ud800path"])
def test_malformed_request_targets_are_rejected_without_raw_url_errors(
    path: str,
) -> None:
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json(path)

    assert caught.value.code == "invalid_request_target"
    assert client.request_count == 0


def test_bounded_json_client_context_manager_closes_its_transport() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, json={"status": "ok"})
    )
    with BoundedJsonClient(
        provider="test",
        base_url="https://example.invalid",
        headers={},
        max_requests=1,
        max_response_bytes=100,
        transport=transport,
    ) as client:
        assert client.get_json("/status") == {"status": "ok"}

    assert client._client.is_closed


def test_connection_failure_is_mapped_without_exposing_transport_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("private proxy detail", request=request)

    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json("/status")

    assert caught.value.code == "network_error"
    assert "private proxy detail" not in str(caught.value)


class _FailingResponseStream(httpx.SyncByteStream):
    def __iter__(self) -> Any:
        raise httpx.ReadError("private stream detail")


class _CloseFailingResponseStream(httpx.SyncByteStream):
    def __iter__(self) -> Any:
        yield b"{}"

    def close(self) -> None:
        raise httpx.CloseError("private close detail")


class _CloseFailingTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"}, request=request)

    def close(self) -> None:
        raise httpx.CloseError("private client close detail")


class _FinallyCloseFailingResponse(httpx.Response):
    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        del chunk_size
        yield b"{}"

    def close(self) -> None:
        raise httpx.CloseError("private final close detail")


def test_stream_failure_is_mapped_and_response_is_closed() -> None:
    responses: list[httpx.Response] = []

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=_FailingResponseStream(),
        )
        responses.append(response)
        return response

    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json("/status")

    assert caught.value.code == "network_error"
    assert "private stream detail" not in str(caught.value)
    assert responses[0].is_closed


@pytest.mark.parametrize(
    ("status", "expected_code"),
    [(404, "not_found"), (200, "network_error")],
)
def test_response_close_failure_never_masks_or_leaks_safe_errors(
    status: int,
    expected_code: str,
) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            status,
            headers={"content-type": "application/json"},
            stream=_CloseFailingResponseStream(),
        )
    )
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=transport,
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json("/status")

    assert caught.value.code == expected_code
    assert "private close detail" not in str(caught.value)


def test_client_close_failure_is_mapped_without_leaking_transport_detail() -> None:
    client = BoundedJsonClient(
        provider="test",
        base_url="https://example.invalid",
        headers={},
        max_requests=1,
        max_response_bytes=100,
        transport=_CloseFailingTransport(),
    )

    with pytest.raises(ApiError) as caught:
        client.close()

    assert caught.value.code == "network_error"
    assert "private client close detail" not in str(caught.value)


def test_context_close_failure_without_active_error_is_safely_mapped() -> None:
    with (
        pytest.raises(ApiError) as caught,
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=_CloseFailingTransport(),
        ),
    ):
        pass

    assert caught.value.code == "network_error"
    assert "private client close detail" not in str(caught.value)


def test_client_close_failure_does_not_mask_an_active_safe_error() -> None:
    with (
        pytest.raises(ApiError) as caught,
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=_CloseFailingTransport(),
        ),
    ):
        raise ApiError("test", 404, "not_found")

    assert caught.value.code == "not_found"
    assert "private client close detail" not in str(caught.value)


def test_talend_context_close_failure_does_not_mask_an_active_safe_error() -> None:
    with (
        pytest.raises(ApiError) as caught,
        TalendApiClient.from_env(transport=_CloseFailingTransport()),
    ):
        raise ApiError("talend", 404, "not_found")

    assert caught.value.code == "not_found"
    assert "private client close detail" not in str(caught.value)


def test_final_response_close_failure_is_safely_mapped() -> None:
    transport = httpx.MockTransport(
        lambda request: _FinallyCloseFailingResponse(
            200,
            headers={"content-type": "application/json"},
            request=request,
        )
    )
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=transport,
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json("/status")

    assert caught.value.code == "network_error"
    assert "private final close detail" not in str(caught.value)


def test_final_response_close_failure_does_not_mask_status_error() -> None:
    transport = httpx.MockTransport(
        lambda request: _FinallyCloseFailingResponse(404, request=request)
    )
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=transport,
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.get_json("/status")

    assert caught.value.code == "not_found"
    assert "private final close detail" not in str(caught.value)


@pytest.mark.parametrize("content", [b"{", b"\xff"])
def test_invalid_json_or_utf8_is_rejected_without_echoing_content(
    content: bytes,
) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=content,
        )
    )
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=100,
            transport=transport,
        ) as client,
        pytest.raises(ApiError, match="invalid_json"),
    ):
        client.get_json("/status")


def test_workspaces_is_get_only_and_sends_pat_in_header() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    with TalendApiClient.from_env(transport=httpx.MockTransport(handler)) as client:
        assert client.list_workspaces(environment_name="Development") == []
        assert client.redaction_secrets == ("talend_pat_super_secret",)

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "GET"
    assert request.url.host == "api.eu.cloud.talend.com"
    assert request.headers["authorization"] == "Bearer talend_pat_super_secret"
    assert request.headers["talend-version"] == TALEND_API_VERSION
    assert request.headers["user-agent"] == "talend-api-github-cli/0.2.1"
    assert request.url.params["query"] == "environment.name==Development"
    assert "limit" not in request.url.params
    assert "offset" not in request.url.params
    assert client._http.trust_env is False


def test_task_and_run_filters_are_normalized_and_forwarded() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"items": []})

    with TalendApiClient.from_env(transport=httpx.MockTransport(handler)) as client:
        assert client.list_tasks(
            workspace_id=" workspace-1 ",
            artifact_id="artifact:2",
            limit=25,
            offset=50,
        ) == {"items": []}
        assert client.list_runs(
            workspace_id="workspace-1",
            status=" EXECUTION_SUCCESSFUL ",
            last_days=3,
            limit=10,
            offset=20,
        ) == {"items": []}

    task_params = seen[0].url.params
    assert task_params["workspaceId"] == "workspace-1"
    assert task_params["artifactId"] == "artifact:2"
    assert task_params["limit"] == "25"
    assert task_params["offset"] == "50"
    run_params = seen[1].url.params
    assert run_params["workspaceId"] == "workspace-1"
    assert run_params["status"] == "execution_successful"
    assert run_params["lastDays"] == "3"
    assert run_params["limit"] == "10"
    assert run_params["offset"] == "20"


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.list_tasks(limit=0),
        lambda client: client.list_tasks(limit=101),
        lambda client: client.list_tasks(offset=-1),
        lambda client: client.list_tasks(offset=1_001),
    ],
)
def test_task_page_boundaries_are_validated_before_network(
    call: Callable[[TalendApiClient], Any],
) -> None:
    def fail_if_called(_: httpx.Request) -> httpx.Response:
        raise AssertionError("network should not be called")

    with (
        TalendApiClient.from_env(
            transport=httpx.MockTransport(fail_if_called)
        ) as client,
        pytest.raises(ValidationError),
    ):
        call(client)


@pytest.mark.parametrize(
    ("status", "headers", "expected_code"),
    [
        (401, {}, "authentication_failed"),
        (403, {}, "forbidden"),
        (404, {}, "not_found"),
        (429, {"retry-after": "12"}, "rate_limited"),
    ],
)
def test_remote_errors_are_classified_and_redacted(
    status: int, headers: dict[str, str], expected_code: str
) -> None:
    body = {"message": "talend_pat_super_secret should never escape"}
    transport = httpx.MockTransport(
        lambda _: httpx.Response(status, headers=headers, json=body)
    )
    with (
        TalendApiClient.from_env(transport=transport) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.list_tasks()
    rendered = str(caught.value)
    assert caught.value.code == expected_code
    assert "talend_pat_super_secret" not in rendered
    assert "should never escape" not in rendered


@pytest.mark.parametrize(
    ("retry_after", "expected"),
    [("9" * 5_000, 86_400), ("99999", 86_400), ("00000", 0)],
)
def test_retry_after_is_safely_bounded_without_integer_conversion_failure(
    retry_after: str,
    expected: int,
) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(429, headers={"retry-after": retry_after})
    )
    with (
        TalendApiClient.from_env(transport=transport) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.list_tasks()

    assert caught.value.code == "rate_limited"
    assert caught.value.retry_after_seconds == expected


@pytest.mark.parametrize(
    ("status", "payload"),
    [
        (202, []),
        (206, {"items": []}),
    ],
)
def test_partial_or_async_success_status_is_not_a_complete_inventory(
    status: int, payload: Any
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json=payload))
    with (
        TalendApiClient.from_env(transport=transport) as client,
        pytest.raises(ApiError, match="unexpected_status"),
    ):
        if status == 202:
            client.list_workspaces()
        else:
            client.list_tasks()


def test_github_style_rate_limit_header_also_maps_403() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(403, headers={"x-ratelimit-remaining": "0"})
    )
    with (
        TalendApiClient.from_env(transport=transport) as client,
        pytest.raises(ApiError, match="rate_limited"),
    ):
        client.list_tasks()


def test_redirect_is_refused_without_second_request() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            302,
            headers={"location": "https://evil.example/steal"},
        )

    with (
        TalendApiClient.from_env(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ApiError, match="redirect_refused"),
    ):
        client.list_workspaces()
    assert calls == 1


def test_transport_rejects_absolute_target_before_forwarding_token() -> None:
    def fail_if_called(_: httpx.Request) -> httpx.Response:
        raise AssertionError("network should not be called")

    with TalendApiClient.from_env(
        transport=httpx.MockTransport(fail_if_called)
    ) as client:
        with pytest.raises(ApiError, match="invalid_request_target"):
            client._http.get_json("https://attacker.invalid/collect")
        with pytest.raises(ApiError, match="invalid_request_target"):
            client._http.get_json("/account/me")
        assert client.request_count == 0


def test_response_and_request_budgets_are_enforced() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, content=json.dumps({"x": "a" * 100}).encode())
    )
    client = TalendApiClient.from_env(
        max_requests=1, max_response_bytes=20, transport=transport
    )
    try:
        with pytest.raises(BudgetExceeded, match="response_byte_budget"):
            client.list_workspaces()
        with pytest.raises(BudgetExceeded, match="request_budget"):
            client.list_workspaces()
    finally:
        client.close()


def test_huge_content_length_is_rejected_without_integer_conversion_failure() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-length": "9" * 5_000},
            content=b"[]",
        )
    )
    with (
        TalendApiClient.from_env(max_response_bytes=100, transport=transport) as client,
        pytest.raises(BudgetExceeded, match="response_byte_budget"),
    ):
        client.list_workspaces()


@pytest.mark.parametrize(
    ("payload", "expected_exception", "expected_code"),
    [
        (b'["\\ud800"]', ApiError, "invalid_json"),
        (b'{"\\ud800": 1}', ApiError, "invalid_json"),
        (b"[NaN]", ApiError, "invalid_json"),
        (b"[1e9999]", ApiError, "invalid_json"),
        (
            (b"[" * 65) + b"0" + (b"]" * 65),
            BudgetExceeded,
            "json_complexity_budget_exceeded",
        ),
        (
            b"[" + (b"0," * 50_000) + b"0]",
            BudgetExceeded,
            "json_complexity_budget_exceeded",
        ),
    ],
    ids=[
        "surrogate-value",
        "surrogate-key",
        "nan",
        "infinite-number",
        "depth-budget",
        "node-budget",
    ],
)
def test_json_parser_rejects_nonstandard_unicode_and_complexity(
    payload: bytes,
    expected_exception: type[Exception],
    expected_code: str,
) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=payload,
        )
    )
    with (
        BoundedJsonClient(
            provider="test",
            base_url="https://example.invalid",
            headers={},
            max_requests=1,
            max_response_bytes=200_000,
            transport=transport,
        ) as client,
        pytest.raises(expected_exception, match=expected_code),
    ):
        client.get_json("/status")


def test_json_parser_accepts_standard_finite_scalar_values() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'[null, true, 1, 1.5, "ok"]',
        )
    )
    with BoundedJsonClient(
        provider="test",
        base_url="https://example.invalid",
        headers={},
        max_requests=1,
        max_response_bytes=100,
        transport=transport,
    ) as client:
        assert client.get_json("/status") == [None, True, 1, 1.5, "ok"]


@pytest.mark.parametrize(
    "call",
    [
        lambda client: client.list_workspaces(environment_name="prod;token==x"),
        lambda client: client.list_tasks(workspace_id="../secret"),
        lambda client: client.list_runs(last_days=11),
        lambda client: client.list_runs(status="not-a-real-status"),
    ],
)
def test_talend_query_validation_happens_before_network(
    call: Callable[[TalendApiClient], Any],
) -> None:
    def fail_if_called(_: httpx.Request) -> httpx.Response:
        raise AssertionError("network should not be called")

    with (
        TalendApiClient.from_env(
            transport=httpx.MockTransport(fail_if_called)
        ) as client,
        pytest.raises(ValidationError),
    ):
        call(client)


def test_wrong_content_type_is_rejected_but_absent_header_is_allowed() -> None:
    responses = iter(
        [
            httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=b"{}",
            ),
            httpx.Response(200, content=b'{"items":[]}'),
        ]
    )
    transport = httpx.MockTransport(lambda _: next(responses))
    with TalendApiClient.from_env(transport=transport) as client:
        with pytest.raises(ApiError, match="invalid_content_type"):
            client.list_tasks()
        assert client.list_tasks() == {"items": []}


@pytest.mark.parametrize(
    ("method_name", "payload", "expected_code"),
    [
        ("list_workspaces", {}, "invalid_workspaces_response"),
        ("list_workspaces", ["not-an-object"], "invalid_workspaces_response"),
        ("list_tasks", [], "invalid_tasks_response"),
        ("list_tasks", {"items": "not-a-list"}, "invalid_tasks_response"),
        ("list_tasks", {"items": [1]}, "invalid_tasks_response"),
        ("list_runs", {"items": None}, "invalid_runs_response"),
        ("list_runs", {"items": ["bad"]}, "invalid_runs_response"),
    ],
)
def test_success_responses_require_documented_record_shapes(
    method_name: str, payload: Any, expected_code: str
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        TalendApiClient.from_env(transport=transport) as client,
        pytest.raises(ApiError, match=expected_code),
    ):
        getattr(client, method_name)()


def test_decompressed_response_bytes_are_bounded() -> None:
    compressed = gzip.compress(json.dumps({"x": "a" * 1_000}).encode())
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-encoding": "gzip",
            },
            content=compressed,
        )
    )
    with (
        TalendApiClient.from_env(max_response_bytes=200, transport=transport) as client,
        pytest.raises(BudgetExceeded, match="response_byte_budget"),
    ):
        client.list_tasks()
