from __future__ import annotations

import base64
from collections.abc import Callable

import httpx
import pytest

from talend_api_starter.errors import ApiError, BudgetExceeded, ValidationError
from talend_api_starter.github import (
    GITHUB_API_VERSION,
    GitHubPublicClient,
    parse_repository_slug,
)
from talend_api_starter.synthetic import SYNTHETIC_ITEM, SYNTHETIC_PROPERTIES

COMMIT_SHA = "a" * 40
ROOT_TREE_SHA = "b" * 40
PROCESS_TREE_SHA = "c" * 40
PROPERTIES_SHA = "d" * 40
ITEM_SHA = "e" * 40
TAG_SHA = "f" * 40


def test_repository_slug_requires_one_owner_repository_separator() -> None:
    assert parse_repository_slug("owner/repository") == ("owner", "repository")
    for value in ("repository", "owner/repository/extra", "../repository"):
        with pytest.raises(ValidationError):
            parse_repository_slug(value)


def fixture_handler(
    requests: list[httpx.Request],
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/git/ref/heads/main"):
            return httpx.Response(
                200, json={"object": {"type": "commit", "sha": COMMIT_SHA}}
            )
        if path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        if path.endswith(f"/git/trees/{ROOT_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {"path": "process", "type": "tree", "sha": PROCESS_TREE_SHA}
                    ],
                },
            )
        if path.endswith(f"/git/trees/{PROCESS_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {
                            "path": "SyntheticCustomers_0.1.properties",
                            "type": "blob",
                            "sha": PROPERTIES_SHA,
                            "size": len(SYNTHETIC_PROPERTIES),
                        },
                        {
                            "path": "SyntheticCustomers_0.1.item",
                            "type": "blob",
                            "sha": ITEM_SHA,
                            "size": len(SYNTHETIC_ITEM),
                        },
                    ],
                },
            )
        if path.endswith(f"/git/blobs/{PROPERTIES_SHA}"):
            return httpx.Response(
                200,
                json={
                    "encoding": "base64",
                    "size": len(SYNTHETIC_PROPERTIES),
                    "content": base64.b64encode(SYNTHETIC_PROPERTIES).decode(),
                },
            )
        if path.endswith(f"/git/blobs/{ITEM_SHA}"):
            return httpx.Response(
                200,
                json={
                    "encoding": "base64",
                    "size": len(SYNTHETIC_ITEM),
                    "content": base64.b64encode(SYNTHETIC_ITEM).decode(),
                },
            )
        raise AssertionError(f"unexpected mocked path: {path}")

    return handler


def test_resolves_ref_commit_tree_and_reads_same_snapshot_blobs() -> None:
    requests: list[httpx.Request] = []
    with GitHubPublicClient(
        transport=httpx.MockTransport(fixture_handler(requests))
    ) as client:
        snapshot = client.fetch_job_files(
            "public-owner", "public-repo", ref="main", path_prefix="process"
        )

    assert snapshot.commit_sha == COMMIT_SHA
    assert snapshot.root_tree_sha == ROOT_TREE_SHA
    assert snapshot.prefix_tree_sha == PROCESS_TREE_SHA
    assert sorted(snapshot.files) == [
        "process/SyntheticCustomers_0.1.item",
        "process/SyntheticCustomers_0.1.properties",
    ]
    assert all(request.method == "GET" for request in requests)
    assert all(
        request.headers["x-github-api-version"] == GITHUB_API_VERSION
        for request in requests
    )
    assert all(
        request.headers["accept"] == "application/vnd.github+json"
        for request in requests
    )
    assert all(
        request.headers["user-agent"] == "talend-api-github-cli/0.2.1"
        for request in requests
    )
    assert not any("/contents/" in request.url.path for request in requests)
    assert not any("recursive" in request.url.params for request in requests)


def test_truncated_tree_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/git/ref/heads/main"):
            return httpx.Response(
                200, json={"object": {"type": "commit", "sha": COMMIT_SHA}}
            )
        if path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        if path.endswith(f"/git/trees/{ROOT_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {"path": "process", "type": "tree", "sha": PROCESS_TREE_SHA}
                    ],
                },
            )
        return httpx.Response(200, json={"truncated": True, "tree": []})

    with (
        GitHubPublicClient(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(BudgetExceeded, match="truncated_tree_refused"),
    ):
        client.fetch_job_files("owner", "repo", path_prefix="process")


@pytest.mark.parametrize(
    ("owner", "repository", "ref", "prefix"),
    [
        ("../owner", "repo", "main", "process"),
        ("owner", "repo.git", "main", "process"),
        ("owner", "repo", "../../main", "process"),
        ("owner", "repo", "main", "../process"),
        ("owner", "repo", "main", "/process"),
        ("owner", "repo", "main", "process\\jobs"),
        ("owner", "repo", "main", "process//jobs"),
        ("owner", "repo", "main", " "),
    ],
)
def test_repository_path_inputs_are_validated_before_network(
    owner: str, repository: str, ref: str, prefix: str
) -> None:
    def fail_if_called(_: httpx.Request) -> httpx.Response:
        raise AssertionError("network should not be called")

    with (
        GitHubPublicClient(transport=httpx.MockTransport(fail_if_called)) as client,
        pytest.raises(ValidationError),
    ):
        client.fetch_job_files(owner, repository, ref=ref, path_prefix=prefix)


def test_github_error_body_is_not_exposed() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(404, json={"message": "TOP_SECRET_TOKEN"})
    )
    with (
        GitHubPublicClient(transport=transport) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.fetch_job_files("owner", "repo")
    assert caught.value.code == "not_found"
    assert "TOP_SECRET_TOKEN" not in str(caught.value)


def test_tree_entry_budget_is_cumulative() -> None:
    requests: list[httpx.Request] = []
    with (
        GitHubPublicClient(
            max_tree_entries=1,
            transport=httpx.MockTransport(fixture_handler(requests)),
        ) as client,
        pytest.raises(BudgetExceeded, match="tree_entry_budget"),
    ):
        client.fetch_job_files("owner", "repo", path_prefix="process")


def test_tree_entry_budget_resets_for_each_snapshot_scan() -> None:
    requests: list[httpx.Request] = []
    with GitHubPublicClient(
        max_tree_entries=3,
        transport=httpx.MockTransport(fixture_handler(requests)),
    ) as client:
        first = client.fetch_job_files("owner", "repo", path_prefix="process")
        second = client.fetch_job_files("owner", "repo", path_prefix="process")
    assert first.files == second.files


def test_commit_sha_skips_ref_lookup() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        if request.url.path.endswith(f"/git/trees/{ROOT_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {"path": "process", "type": "tree", "sha": PROCESS_TREE_SHA}
                    ],
                },
            )
        if request.url.path.endswith(f"/git/trees/{PROCESS_TREE_SHA}"):
            return httpx.Response(200, json={"truncated": False, "tree": []})
        raise AssertionError(request.url.path)

    with GitHubPublicClient(transport=httpx.MockTransport(handler)) as client:
        snapshot = client.fetch_job_files(
            "owner", "repo", ref=COMMIT_SHA, path_prefix="process"
        )
    assert snapshot.commit_sha == COMMIT_SHA
    assert not any("/git/ref/" in request.url.path for request in requests)


def test_annotated_tag_is_peeled_to_commit() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/git/ref/tags/v1.0.0"):
            return httpx.Response(200, json={"object": {"type": "tag", "sha": TAG_SHA}})
        if path.endswith(f"/git/tags/{TAG_SHA}"):
            return httpx.Response(
                200, json={"object": {"type": "commit", "sha": COMMIT_SHA}}
            )
        if path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        if path.endswith(f"/git/trees/{ROOT_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {"path": "process", "type": "tree", "sha": PROCESS_TREE_SHA}
                    ],
                },
            )
        if path.endswith(f"/git/trees/{PROCESS_TREE_SHA}"):
            return httpx.Response(200, json={"truncated": False, "tree": []})
        raise AssertionError(path)

    with GitHubPublicClient(transport=httpx.MockTransport(handler)) as client:
        snapshot = client.fetch_job_files(
            "owner", "repo", ref="tags/v1.0.0", path_prefix="process"
        )
    assert snapshot.commit_sha == COMMIT_SHA
    assert any("/git/tags/" in request.url.path for request in requests)


def test_bare_tag_falls_back_after_missing_branch() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/git/ref/heads/v1.0.0"):
            return httpx.Response(404, json={"message": "not found"})
        if path.endswith("/git/ref/tags/v1.0.0"):
            return httpx.Response(
                200, json={"object": {"type": "commit", "sha": COMMIT_SHA}}
            )
        if path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        if path.endswith(f"/git/trees/{ROOT_TREE_SHA}"):
            return httpx.Response(
                200,
                json={
                    "truncated": False,
                    "tree": [
                        {"path": "process", "type": "tree", "sha": PROCESS_TREE_SHA}
                    ],
                },
            )
        if path.endswith(f"/git/trees/{PROCESS_TREE_SHA}"):
            return httpx.Response(200, json={"truncated": False, "tree": []})
        raise AssertionError(path)

    with GitHubPublicClient(
        transport=httpx.MockTransport(handler), retry_delay_seconds=0
    ) as client:
        snapshot = client.fetch_job_files(
            "owner", "repo", ref="v1.0.0", path_prefix="process"
        )

    assert snapshot.ref == "tags/v1.0.0"
    requested_paths = [request.url.path for request in requests]
    assert any(path.endswith("/git/ref/heads/v1.0.0") for path in requested_paths)
    assert any(path.endswith("/git/ref/tags/v1.0.0") for path in requested_paths)


def test_transient_gateway_failures_are_retried_within_budget() -> None:
    requests: list[httpx.Request] = []
    normal_handler = fixture_handler(requests)
    ref_attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal ref_attempts
        if request.url.path.endswith("/git/ref/heads/main"):
            ref_attempts += 1
            if ref_attempts <= 2:
                requests.append(request)
                return httpx.Response(504, json={"message": "temporary gateway error"})
        return normal_handler(request)

    with GitHubPublicClient(
        transport=httpx.MockTransport(handler), retry_delay_seconds=0
    ) as client:
        snapshot = client.fetch_job_files(
            "owner", "repo", ref="main", path_prefix="process"
        )

    assert snapshot.commit_sha == COMMIT_SHA
    assert ref_attempts == 3
    assert client._http.request_count == len(requests)


@pytest.mark.parametrize("provider_status", [502, 503, 504])
def test_transient_gateway_retry_exhaustion_is_safe_and_bounded(
    provider_status: int,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            provider_status, json={"message": "do not expose this body"}
        )

    with (
        GitHubPublicClient(
            transport=httpx.MockTransport(handler),
            max_transient_retries=1,
            retry_delay_seconds=0,
        ) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.fetch_job_files("owner", "repo", ref="main", path_prefix="process")

    assert caught.value.code == "temporarily_unavailable"
    assert caught.value.status_code == provider_status
    assert len(requests) == 2
    assert "do not expose" not in str(caught.value)


def test_request_budget_also_caps_transient_retry_attempts() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(504, json={"message": "temporary"})

    with (
        GitHubPublicClient(
            max_requests=2,
            max_transient_retries=3,
            retry_delay_seconds=0,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(BudgetExceeded, match="request_budget_exceeded"),
    ):
        client.fetch_job_files("owner", "repo", ref="main", path_prefix="process")

    assert len(requests) == 2


@pytest.mark.parametrize(
    ("retries", "delay"),
    [(-1, 0), (4, 0), (0, -0.01), (0, 5.01)],
)
def test_transient_retry_policy_is_bounded(retries: int, delay: float) -> None:
    with pytest.raises(ValueError):
        GitHubPublicClient(
            max_transient_retries=retries,
            retry_delay_seconds=delay,
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
        )
