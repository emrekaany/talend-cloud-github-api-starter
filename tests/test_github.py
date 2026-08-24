from __future__ import annotations

import base64
from collections.abc import Callable

import httpx
import pytest

from talend_api_starter.errors import ApiError, BudgetExceeded, ValidationError
from talend_api_starter.github import (
    GITHUB_API_VERSION,
    GitHubPublicClient,
    normalize_git_ref,
    parse_repository_slug,
)
from talend_api_starter.synthetic import SYNTHETIC_ITEM, SYNTHETIC_PROPERTIES

COMMIT_SHA = "a" * 40
ROOT_TREE_SHA = "b" * 40
PROCESS_TREE_SHA = "c" * 40
PROPERTIES_SHA = "d" * 40
ITEM_SHA = "e" * 40
TAG_SHA = "f" * 40


class _CloseFailingTransport(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={}, request=request)

    def close(self) -> None:
        raise httpx.CloseError("private GitHub client close detail")


def test_repository_slug_requires_one_owner_repository_separator() -> None:
    assert parse_repository_slug("owner/repository") == ("owner", "repository")
    for value in ("repository", "owner/repository/extra", "../repository"):
        with pytest.raises(ValidationError):
            parse_repository_slug(value)


def test_explicit_ref_prefix_is_normalized_without_changing_its_identity() -> None:
    assert normalize_git_ref("refs/tags/v1.2.3") == "tags/v1.2.3"


@pytest.mark.parametrize("ref", ["refs/foo", "refs/tags", "refs/heads"])
def test_malformed_explicit_ref_names_are_rejected_before_network(ref: str) -> None:
    with pytest.raises(ValidationError, match="Invalid GitHub ref"):
        normalize_git_ref(ref)


@pytest.mark.parametrize("path_prefix", ["process/\ud800", "process/bad\x7fpath"])
def test_path_prefix_requires_valid_printable_unicode(path_prefix: str) -> None:
    with pytest.raises(ValidationError, match="Invalid repository path prefix"):
        GitHubPublicClient().fetch_job_files(
            "owner", "repository", path_prefix=path_prefix
        )


def test_github_context_close_failure_does_not_mask_an_active_safe_error() -> None:
    with (
        pytest.raises(ApiError) as caught,
        GitHubPublicClient(transport=_CloseFailingTransport()),
    ):
        raise ApiError("github", 404, "not_found")

    assert caught.value.code == "not_found"
    assert "private GitHub client close detail" not in str(caught.value)


def test_github_close_failure_is_safely_mapped() -> None:
    client = GitHubPublicClient(transport=_CloseFailingTransport())

    with pytest.raises(ApiError) as caught:
        client.close()

    assert caught.value.code == "network_error"
    assert "private GitHub client close detail" not in str(caught.value)


@pytest.mark.parametrize(
    "budget_name",
    [
        "max_tree_entries",
        "max_depth",
        "max_blobs",
        "max_blob_bytes",
        "max_total_blob_bytes",
    ],
)
def test_every_github_scan_budget_must_be_positive(budget_name: str) -> None:
    with pytest.raises(ValueError, match="scan budgets must be positive"):
        GitHubPublicClient(**{budget_name: 0})


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


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ([], "invalid_ref_response"),
        ({"object": {"type": "commit", "sha": "not-a-sha"}}, "invalid_ref_response"),
        (
            {"object": {"type": "tree", "sha": COMMIT_SHA}},
            "ref_target_not_commit",
        ),
    ],
)
def test_ref_responses_require_a_commit_or_annotated_tag_target(
    payload: object, expected_code: str
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        GitHubPublicClient(transport=transport) as client,
        pytest.raises(ApiError) as caught,
    ):
        client.resolve_ref("owner", "repo", "main")

    assert caught.value.code == expected_code


def test_public_resolve_ref_returns_the_commit_and_root_tree() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/git/ref/heads/main"):
            return httpx.Response(
                200, json={"object": {"type": "commit", "sha": COMMIT_SHA}}
            )
        if request.url.path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return httpx.Response(200, json={"tree": {"sha": ROOT_TREE_SHA}})
        raise AssertionError(request.url.path)

    with GitHubPublicClient(transport=httpx.MockTransport(handler)) as client:
        assert client.resolve_ref("owner", "repo", "main") == (
            COMMIT_SHA,
            ROOT_TREE_SHA,
        )


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
    "payload",
    [
        {"tree": []},
        {"truncated": False, "tree": {}},
        {
            "truncated": False,
            "tree": [{"path": "nested/name", "type": "blob", "sha": ITEM_SHA}],
        },
        {
            "truncated": False,
            "tree": [{"path": "bad\x7fname", "type": "blob", "sha": ITEM_SHA}],
        },
        {
            "truncated": False,
            "tree": [{"path": "a" * 1_025, "type": "blob", "sha": ITEM_SHA}],
        },
        {
            "truncated": False,
            "tree": [
                {"path": "duplicate", "type": "blob", "sha": ITEM_SHA},
                {"path": "duplicate", "type": "blob", "sha": ITEM_SHA},
            ],
        },
    ],
)
def test_tree_responses_require_complete_non_recursive_git_shapes(
    payload: object,
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        GitHubPublicClient(transport=transport) as client,
        pytest.raises(ApiError, match="invalid_tree_response"),
    ):
        client._get_tree("owner", "repo", ROOT_TREE_SHA)


@pytest.mark.parametrize(
    ("entries", "expected_exception", "expected_message"),
    [
        ([], ApiError, "path_prefix_not_found"),
        (
            [{"path": "process", "type": "blob", "sha": ITEM_SHA}],
            ValidationError,
            "must identify a tree",
        ),
    ],
)
def test_path_prefix_must_exist_and_resolve_to_a_tree(
    entries: list[dict[str, object]],
    expected_exception: type[Exception],
    expected_message: str,
) -> None:
    payload = {"truncated": False, "tree": entries}
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        GitHubPublicClient(transport=transport) as client,
        pytest.raises(expected_exception, match=expected_message),
    ):
        client._descend_prefix("owner", "repo", ROOT_TREE_SHA, "process")


def test_nested_tree_depth_budget_is_enforced_before_unbounded_walk() -> None:
    payload = {
        "truncated": False,
        "tree": [{"path": "nested", "type": "tree", "sha": PROCESS_TREE_SHA}],
    }
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        GitHubPublicClient(max_depth=1, transport=transport) as client,
        pytest.raises(BudgetExceeded, match="tree_depth_budget_exceeded"),
    ):
        client._scan_prefix_tree("owner", "repo", ROOT_TREE_SHA, "process")


def test_scan_ignores_non_talend_blobs_and_submodule_entries() -> None:
    payload = {
        "truncated": False,
        "tree": [
            {"path": "README.md", "type": "blob", "sha": ITEM_SHA, "size": 1},
            {"path": "vendor", "type": "commit", "sha": COMMIT_SHA},
        ],
    }
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with GitHubPublicClient(transport=transport) as client:
        assert client._scan_prefix_tree("owner", "repo", ROOT_TREE_SHA, "process") == []


@pytest.mark.parametrize(
    ("entries", "client_kwargs", "expected_message"),
    [
        (
            [{"path": "large.item", "type": "blob", "sha": ITEM_SHA, "size": 2}],
            {"max_blob_bytes": 1},
            "blob_byte_budget_exceeded",
        ),
        (
            [
                {"path": "one.item", "type": "blob", "sha": ITEM_SHA, "size": 1},
                {
                    "path": "two.properties",
                    "type": "blob",
                    "sha": PROPERTIES_SHA,
                    "size": 1,
                },
            ],
            {"max_blobs": 1},
            "blob_count_budget_exceeded",
        ),
    ],
)
def test_tree_metadata_is_bounded_before_any_blob_download(
    entries: list[dict[str, object]],
    client_kwargs: dict[str, int],
    expected_message: str,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"truncated": False, "tree": entries})

    with (
        GitHubPublicClient(
            transport=httpx.MockTransport(handler), **client_kwargs
        ) as client,
        pytest.raises(BudgetExceeded, match=expected_message),
    ):
        client._scan_prefix_tree("owner", "repo", ROOT_TREE_SHA, "process")

    assert all("/git/blobs/" not in request.url.path for request in requests)


@pytest.mark.parametrize(
    (
        "payload",
        "declared_size",
        "client_kwargs",
        "expected_exception",
        "expected_message",
    ),
    [
        (
            {"encoding": "utf-8", "content": "plain text"},
            None,
            {},
            ApiError,
            "unsupported_blob_encoding",
        ),
        (
            {"encoding": "base64", "content": "%%%"},
            None,
            {},
            ApiError,
            "invalid_blob_response",
        ),
        (
            {"encoding": "base64", "content": "eA==", "size": 2},
            None,
            {},
            ApiError,
            "blob_size_mismatch",
        ),
        (
            {"encoding": "base64", "content": "eA==", "size": 1},
            2,
            {},
            ApiError,
            "blob_size_mismatch",
        ),
        (
            {"encoding": "base64", "content": "eHg="},
            None,
            {"max_blob_bytes": 1},
            BudgetExceeded,
            "blob_byte_budget_exceeded",
        ),
    ],
)
def test_blob_payloads_require_base64_and_consistent_bounded_sizes(
    payload: object,
    declared_size: int | None,
    client_kwargs: dict[str, int],
    expected_exception: type[Exception],
    expected_message: str,
) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    with (
        GitHubPublicClient(
            transport=transport,
            **client_kwargs,
        ) as client,
        pytest.raises(expected_exception, match=expected_message),
    ):
        client._fetch_blobs(
            "owner", "repo", [("process/Synthetic.item", ITEM_SHA, declared_size)]
        )


def test_total_decoded_blob_bytes_are_bounded_across_files() -> None:
    payload = {
        "encoding": "base64",
        "content": base64.b64encode(b"xx").decode(),
        "size": 2,
    }
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    blobs = [
        ("process/one.item", ITEM_SHA, 2),
        ("process/two.properties", PROPERTIES_SHA, 2),
    ]
    with (
        GitHubPublicClient(
            max_blob_bytes=2,
            max_total_blob_bytes=3,
            transport=transport,
        ) as client,
        pytest.raises(BudgetExceeded, match="total_blob_byte_budget_exceeded"),
    ):
        client._fetch_blobs("owner", "repo", blobs)


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


def test_annotated_tag_must_eventually_target_a_commit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/git/ref/tags/v1.0.0"):
            return httpx.Response(200, json={"object": {"type": "tag", "sha": TAG_SHA}})
        if request.url.path.endswith(f"/git/tags/{TAG_SHA}"):
            return httpx.Response(
                200, json={"object": {"type": "blob", "sha": ITEM_SHA}}
            )
        raise AssertionError(request.url.path)

    with (
        GitHubPublicClient(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ApiError, match="tag_target_not_commit"),
    ):
        client.resolve_ref("owner", "repo", "tags/v1.0.0")


def test_annotated_tag_chain_has_a_hard_depth_limit() -> None:
    tag_requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal tag_requests
        if request.url.path.endswith("/git/ref/tags/v1.0.0"):
            return httpx.Response(200, json={"object": {"type": "tag", "sha": TAG_SHA}})
        if request.url.path.endswith(f"/git/tags/{TAG_SHA}"):
            tag_requests += 1
            return httpx.Response(200, json={"object": {"type": "tag", "sha": TAG_SHA}})
        raise AssertionError(request.url.path)

    with (
        GitHubPublicClient(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(BudgetExceeded, match="annotated_tag_depth_budget_exceeded"),
    ):
        client.resolve_ref("owner", "repo", "tags/v1.0.0")

    assert tag_requests == 5


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


def test_transient_gateway_failures_are_retried_within_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []
    sleep_delays: list[float] = []
    normal_handler = fixture_handler(requests)
    ref_attempts = 0

    monkeypatch.setattr("talend_api_starter.github.time.sleep", sleep_delays.append)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal ref_attempts
        if request.url.path.endswith("/git/ref/heads/main"):
            ref_attempts += 1
            if ref_attempts <= 2:
                requests.append(request)
                return httpx.Response(504, json={"message": "temporary gateway error"})
        return normal_handler(request)

    with GitHubPublicClient(
        transport=httpx.MockTransport(handler), retry_delay_seconds=0.25
    ) as client:
        snapshot = client.fetch_job_files(
            "owner", "repo", ref="main", path_prefix="process"
        )

    assert snapshot.commit_sha == COMMIT_SHA
    assert ref_attempts == 3
    assert sleep_delays == [0.25, 0.5]
    assert client.request_count == len(requests)


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
