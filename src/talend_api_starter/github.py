"""Bounded reader for Talend job files in a public GitHub repository."""

from __future__ import annotations

import base64
import binascii
import re
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from ._version import USER_AGENT
from .errors import ApiError, BudgetExceeded, ValidationError
from .http import DEFAULT_TIMEOUT, BoundedJsonClient

# Current version shown by the official GitHub REST documentation on 2026-08-11.
GITHUB_API_VERSION = "2026-03-10"
GITHUB_API_BASE_URL = "https://api.github.com"

_OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
_INTERESTING_SUFFIXES = (".properties", ".item")


@dataclass(frozen=True, slots=True)
class GitHubSnapshot:
    owner: str
    repository: str
    ref: str
    commit_sha: str
    root_tree_sha: str
    prefix_tree_sha: str
    path_prefix: str
    files: Mapping[str, bytes]


def _validate_owner_repo(value: str, field: str) -> str:
    value = value.strip()
    if not _OWNER_REPO_RE.fullmatch(value) or ".." in value:
        raise ValidationError(f"Invalid GitHub {field}")
    if field == "repository" and value.endswith(".git"):
        raise ValidationError("GitHub repository name must not end in .git")
    return value


def normalize_git_ref(ref: str) -> str:
    ref = ref.strip()
    if _SHA_RE.fullmatch(ref):
        return ref.lower()
    if ref.startswith("refs/"):
        ref = ref[5:]
    if not (ref.startswith("heads/") or ref.startswith("tags/")):
        ref = f"heads/{ref}"
    if (
        not _REF_RE.fullmatch(ref)
        or "//" in ref
        or ref.endswith("/")
        or any(segment in ("", ".", "..") for segment in ref.split("/"))
    ):
        raise ValidationError("Invalid GitHub ref")
    return ref


def validate_path_prefix(path_prefix: str) -> str:
    path_prefix = path_prefix.strip()
    if not path_prefix:
        raise ValidationError("Repository path prefix must not be empty")
    if (
        path_prefix.startswith("/")
        or path_prefix.endswith("/")
        or "//" in path_prefix
        or "\\" in path_prefix
        or len(path_prefix.encode("utf-8")) > 1_024
    ):
        raise ValidationError("Invalid repository path prefix")
    for segment in path_prefix.split("/"):
        if segment in ("", ".", "..") or any(ord(char) < 32 for char in segment):
            raise ValidationError("Invalid repository path prefix")
    return path_prefix


def parse_repository_slug(value: str) -> tuple[str, str]:
    value = value.strip()
    if value.count("/") != 1:
        raise ValidationError("Repository must use OWNER/REPOSITORY format")
    owner, repository = value.split("/", 1)
    return (
        _validate_owner_repo(owner, "owner"),
        _validate_owner_repo(repository, "repository"),
    )


def _required_dict(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ApiError("github", 200, code)
    return value


def _required_sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise ApiError("github", 200, code)
    return value.lower()


class GitHubPublicClient:
    """Anonymous, GET-only client for public GitHub Git Database objects."""

    def __init__(
        self,
        *,
        max_requests: int = 40,
        max_response_bytes: int = 2_000_000,
        max_tree_entries: int = 2_000,
        max_depth: int = 8,
        max_blobs: int = 100,
        max_blob_bytes: int = 1_000_000,
        max_total_blob_bytes: int = 5_000_000,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        budgets = (
            max_tree_entries,
            max_depth,
            max_blobs,
            max_blob_bytes,
            max_total_blob_bytes,
        )
        if any(value < 1 for value in budgets):
            raise ValueError("GitHub scan budgets must be positive")
        self.max_tree_entries = max_tree_entries
        self.max_depth = max_depth
        self.max_blobs = max_blobs
        self.max_blob_bytes = max_blob_bytes
        self.max_total_blob_bytes = max_total_blob_bytes
        self._tree_entries_seen = 0
        self._http = BoundedJsonClient(
            provider="github",
            base_url=GITHUB_API_BASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": USER_AGENT,
            },
            max_requests=max_requests,
            max_response_bytes=max_response_bytes,
            timeout=timeout,
            transport=transport,
        )

    @property
    def request_count(self) -> int:
        return self._http.request_count

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> GitHubPublicClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def resolve_ref(self, owner: str, repository: str, ref: str) -> tuple[str, str]:
        """Resolve ref -> commit SHA -> root tree SHA."""

        owner = _validate_owner_repo(owner, "owner")
        repository = _validate_owner_repo(repository, "repository")
        normalized_ref = normalize_git_ref(ref)
        root = f"/repos/{owner}/{repository}"
        if _SHA_RE.fullmatch(normalized_ref):
            commit_sha = normalized_ref
        else:
            ref_payload = _required_dict(
                self._http.get_json(
                    f"{root}/git/ref/{quote(normalized_ref, safe='/')}"
                ),
                "invalid_ref_response",
            )
            ref_object = _required_dict(
                ref_payload.get("object"), "invalid_ref_response"
            )
            object_type = ref_object.get("type")
            object_sha = _required_sha(ref_object.get("sha"), "invalid_ref_response")
            if object_type == "commit":
                commit_sha = object_sha
            elif object_type == "tag":
                commit_sha = self._peel_annotated_tag(root, object_sha)
            else:
                raise ApiError("github", 200, "ref_target_not_commit")
        commit = _required_dict(
            self._http.get_json(f"{root}/git/commits/{commit_sha}"),
            "invalid_commit_response",
        )
        tree = _required_dict(commit.get("tree"), "invalid_commit_response")
        tree_sha = _required_sha(tree.get("sha"), "invalid_commit_response")
        return commit_sha, tree_sha

    def _peel_annotated_tag(self, repository_root: str, tag_sha: str) -> str:
        """Peel a bounded annotated-tag chain until it reaches a commit."""

        current_sha = tag_sha
        for _ in range(5):
            tag_payload = _required_dict(
                self._http.get_json(f"{repository_root}/git/tags/{current_sha}"),
                "invalid_tag_response",
            )
            target = _required_dict(tag_payload.get("object"), "invalid_tag_response")
            target_type = target.get("type")
            target_sha = _required_sha(target.get("sha"), "invalid_tag_response")
            if target_type == "commit":
                return target_sha
            if target_type != "tag":
                raise ApiError("github", 200, "tag_target_not_commit")
            current_sha = target_sha
        raise BudgetExceeded("github: annotated_tag_depth_budget_exceeded")

    def fetch_job_files(
        self,
        owner: str,
        repository: str,
        *,
        ref: str = "main",
        path_prefix: str = "process",
    ) -> GitHubSnapshot:
        owner = _validate_owner_repo(owner, "owner")
        repository = _validate_owner_repo(repository, "repository")
        normalized_ref = normalize_git_ref(ref)
        path_prefix = validate_path_prefix(path_prefix)
        self._tree_entries_seen = 0
        commit_sha, root_tree_sha = self.resolve_ref(owner, repository, normalized_ref)
        prefix_tree_sha = self._descend_prefix(
            owner, repository, root_tree_sha, path_prefix
        )
        blobs = self._scan_prefix_tree(owner, repository, prefix_tree_sha, path_prefix)
        files = self._fetch_blobs(owner, repository, blobs)
        return GitHubSnapshot(
            owner=owner,
            repository=repository,
            ref=normalized_ref,
            commit_sha=commit_sha,
            root_tree_sha=root_tree_sha,
            prefix_tree_sha=prefix_tree_sha,
            path_prefix=path_prefix,
            files=files,
        )

    def _get_tree(
        self, owner: str, repository: str, tree_sha: str
    ) -> list[dict[str, Any]]:
        payload = _required_dict(
            self._http.get_json(f"/repos/{owner}/{repository}/git/trees/{tree_sha}"),
            "invalid_tree_response",
        )
        if payload.get("truncated") is True:
            raise BudgetExceeded("github: truncated_tree_refused")
        if payload.get("truncated") is not False:
            raise ApiError("github", 200, "invalid_tree_response")
        raw_entries = payload.get("tree")
        if not isinstance(raw_entries, list):
            raise ApiError("github", 200, "invalid_tree_response")
        entries: list[dict[str, Any]] = []
        for raw in raw_entries:
            entry = _required_dict(raw, "invalid_tree_response")
            path = entry.get("path")
            kind = entry.get("type")
            sha = entry.get("sha")
            if (
                not isinstance(path, str)
                or not path
                or "/" in path
                or "\\" in path
                or path in (".", "..")
                or any(ord(char) < 32 for char in path)
                or kind not in ("blob", "tree", "commit")
            ):
                raise ApiError("github", 200, "invalid_tree_response")
            entry = dict(entry)
            entry["sha"] = _required_sha(sha, "invalid_tree_response")
            entries.append(entry)
        self._tree_entries_seen += len(entries)
        if self._tree_entries_seen > self.max_tree_entries:
            raise BudgetExceeded("github: tree_entry_budget_exceeded")
        return entries

    def _descend_prefix(
        self,
        owner: str,
        repository: str,
        root_tree_sha: str,
        path_prefix: str,
    ) -> str:
        current_sha = root_tree_sha
        if not path_prefix:
            return current_sha
        for segment in path_prefix.split("/"):
            entries = self._get_tree(owner, repository, current_sha)
            match = next((entry for entry in entries if entry["path"] == segment), None)
            if match is None:
                raise ApiError("github", 404, "path_prefix_not_found")
            if match["type"] != "tree":
                raise ValidationError("Repository path prefix must identify a tree")
            current_sha = str(match["sha"])
        return current_sha

    def _scan_prefix_tree(
        self,
        owner: str,
        repository: str,
        prefix_tree_sha: str,
        path_prefix: str,
    ) -> list[tuple[str, str, int | None]]:
        queue: deque[tuple[str, str, int]] = deque([(prefix_tree_sha, path_prefix, 0)])
        blobs: list[tuple[str, str, int | None]] = []
        while queue:
            tree_sha, parent_path, depth = queue.popleft()
            entries = self._get_tree(owner, repository, tree_sha)
            for entry in entries:
                relative_path = (
                    f"{parent_path}/{entry['path']}"
                    if parent_path
                    else str(entry["path"])
                )
                if entry["type"] == "tree":
                    if depth >= self.max_depth:
                        raise BudgetExceeded("github: tree_depth_budget_exceeded")
                    queue.append((str(entry["sha"]), relative_path, depth + 1))
                elif entry["type"] == "blob" and relative_path.endswith(
                    _INTERESTING_SUFFIXES
                ):
                    raw_size = entry.get("size")
                    size = (
                        raw_size
                        if isinstance(raw_size, int) and raw_size >= 0
                        else None
                    )
                    if size is not None and size > self.max_blob_bytes:
                        raise BudgetExceeded("github: blob_byte_budget_exceeded")
                    blobs.append((relative_path, str(entry["sha"]), size))
                    if len(blobs) > self.max_blobs:
                        raise BudgetExceeded("github: blob_count_budget_exceeded")
        return sorted(blobs)

    def _fetch_blobs(
        self,
        owner: str,
        repository: str,
        blobs: list[tuple[str, str, int | None]],
    ) -> dict[str, bytes]:
        result: dict[str, bytes] = {}
        total_bytes = 0
        for path, sha, declared_size in blobs:
            payload = _required_dict(
                self._http.get_json(f"/repos/{owner}/{repository}/git/blobs/{sha}"),
                "invalid_blob_response",
            )
            if payload.get("encoding") != "base64" or not isinstance(
                payload.get("content"), str
            ):
                raise ApiError("github", 200, "unsupported_blob_encoding")
            compact = "".join(str(payload["content"]).split())
            try:
                content = base64.b64decode(compact, validate=True)
            except (binascii.Error, ValueError):
                raise ApiError("github", 200, "invalid_blob_response") from None
            response_size = payload.get("size")
            if isinstance(response_size, int) and response_size != len(content):
                raise ApiError("github", 200, "blob_size_mismatch")
            if declared_size is not None and declared_size != len(content):
                raise ApiError("github", 200, "blob_size_mismatch")
            if len(content) > self.max_blob_bytes:
                raise BudgetExceeded("github: blob_byte_budget_exceeded")
            total_bytes += len(content)
            if total_bytes > self.max_total_blob_bytes:
                raise BudgetExceeded("github: total_blob_byte_budget_exceeded")
            result[path] = content
        return result
