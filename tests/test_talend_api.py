"""Contract and security tests for the GET-only Talend API client."""

from __future__ import annotations

import gzip
import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from talend_api_starter.errors import (
    ApiError,
    BudgetExceeded,
    ConfigurationError,
    ValidationError,
)
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


def test_documented_region_pattern_is_not_a_closed_enum() -> None:
    url = "https://api.ca-central.cloud.talend.com"
    assert validate_official_talend_base_url(url) == url


def test_workspaces_is_get_only_and_sends_pat_in_header() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    with TalendApiClient.from_env(transport=httpx.MockTransport(handler)) as client:
        assert client.list_workspaces(environment_name="Development") == []

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
    with TalendApiClient.from_env(
        max_requests=1, max_response_bytes=20, transport=transport
    ) as client:
        with pytest.raises(BudgetExceeded, match="response_byte_budget"):
            client.list_workspaces()
        with pytest.raises(BudgetExceeded, match="request_budget"):
            client.list_workspaces()


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
