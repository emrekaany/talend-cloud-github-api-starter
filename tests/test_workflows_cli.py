from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

import talend_api_starter.cli as cli
from talend_api_starter.github import GitHubSnapshot
from talend_api_starter.outputs import OutputPaths
from talend_api_starter.synthetic import synthetic_files, write_synthetic_fixtures
from talend_api_starter.talend_api import TalendApiClient
from talend_api_starter.workflows import (
    save_github_jobs,
    save_local_jobs,
    save_talend_inventory,
)

runner = CliRunner()


class FakeGitHubClient:
    def fetch_job_files(
        self,
        owner: str,
        repository: str,
        *,
        ref: str,
        path_prefix: str,
    ) -> GitHubSnapshot:
        return GitHubSnapshot(
            owner=owner,
            repository=repository,
            ref=f"heads/{ref}",
            commit_sha="a" * 40,
            root_tree_sha="b" * 40,
            prefix_tree_sha="c" * 40,
            path_prefix=path_prefix,
            files=synthetic_files(path_prefix),
        )


class FakeTalendClient:
    region = "synthetic-region"
    redaction_secrets: tuple[str, ...] = ()

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def list_workspaces(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(("workspaces", kwargs))
        return [{"id": "private-workspace", "name": "Local Workspace"}]

    def list_tasks(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("tasks", kwargs))
        return {"items": [{"id": "private-task", "status": "READY"}]}

    def list_runs(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("runs", kwargs))
        return {"items": [{"executionId": "private-run", "status": "executing"}]}


class ContextClient:
    def __enter__(self) -> ContextClient:
        return self

    def __exit__(self, *_: object) -> None:
        return None


def test_reusable_github_workflow_parses_and_writes(tmp_path: Path) -> None:
    paths = save_github_jobs(
        FakeGitHubClient(),  # type: ignore[arg-type]
        owner="owner",
        repository="repository",
        ref="main",
        path_prefix="process/demo",
        destination=tmp_path,
    )
    assert paths.local_view.is_file()
    assert paths.share_safe.is_file()
    assert "SyntheticCustomers" in paths.local_view.read_text(encoding="utf-8")
    assert "SyntheticCustomers" not in paths.share_safe.read_text(encoding="utf-8")


def test_reusable_talend_workflows_cover_all_resources(tmp_path: Path) -> None:
    client = FakeTalendClient()
    for resource in ("workspaces", "tasks", "runs"):
        paths = save_talend_inventory(
            client,  # type: ignore[arg-type]
            resource=resource,
            destination=tmp_path / resource,
            workspace_id="workspace-1",
            artifact_id="artifact-1",
            environment_name="Development",
            status="executing",
            last_days=2,
            limit=25,
            offset=5,
        )
        assert paths.local_view.is_file()
        assert paths.share_safe.is_file()
    assert [name for name, _ in client.calls] == ["workspaces", "tasks", "runs"]


def test_reusable_talend_workflow_rejects_unknown_resource(tmp_path: Path) -> None:
    client = FakeTalendClient()

    with pytest.raises(ValueError, match="Unsupported Talend API resource"):
        save_talend_inventory(
            client,  # type: ignore[arg-type]
            resource="secrets",
            destination=tmp_path,
        )

    assert client.calls == []
    assert not tmp_path.joinpath("local_view.json").exists()
    assert not tmp_path.joinpath("share_safe.json").exists()


def test_talend_workflow_redacts_normalized_environment_token(
    tmp_path: Path, monkeypatch: Any
) -> None:
    class EchoTokenClient(FakeTalendClient):
        redaction_secrets = ("secret-token",)

        def list_workspaces(self, **kwargs: Any) -> list[dict[str, Any]]:
            self.calls.append(("workspaces", kwargs))
            return [{"message": "provider echoed secret-token"}]

    monkeypatch.setenv("TALEND_TOKEN", "  secret-token  ")
    paths = save_talend_inventory(
        EchoTokenClient(),  # type: ignore[arg-type]
        resource="workspaces",
        destination=tmp_path,
    )
    local_text = paths.local_view.read_text(encoding="utf-8")
    assert "secret-token" not in local_text
    assert "[REDACTED]" in local_text


def test_talend_workflow_redacts_token_captured_when_client_was_created(
    tmp_path: Path, monkeypatch: Any
) -> None:
    original_token = "original-secret-token"
    monkeypatch.setenv("TALEND_TOKEN", original_token)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200, json=[{"message": f"provider echoed {original_token}"}]
        )
    )
    with TalendApiClient(
        "https://api.eu.cloud.talend.com", transport=transport
    ) as client:
        monkeypatch.setenv("TALEND_TOKEN", "replacement-token")
        paths = save_talend_inventory(
            client,
            resource="workspaces",
            destination=tmp_path,
        )
    local_text = paths.local_view.read_text(encoding="utf-8")
    assert original_token not in local_text
    assert "[REDACTED]" in local_text


def test_fixture_writer_uses_package_fixture_bytes(tmp_path: Path) -> None:
    properties_path, item_path = write_synthetic_fixtures(tmp_path)
    expected = synthetic_files("")
    assert properties_path.read_bytes() == expected[properties_path.name]
    assert item_path.read_bytes() == expected[item_path.name]


def test_reusable_local_workflow_is_network_free(tmp_path: Path) -> None:
    root = tmp_path / "project"
    fixture_directory = root / "process" / "demo"
    write_synthetic_fixtures(fixture_directory)

    paths = save_local_jobs(
        root,
        path_prefix="process",
        destination=tmp_path / "output",
    )

    assert "SyntheticCustomers" in paths.local_view.read_text(encoding="utf-8")
    assert "SyntheticCustomers" not in paths.share_safe.read_text(encoding="utf-8")


def test_cli_live_command_shapes_without_network(
    tmp_path: Path, monkeypatch: Any
) -> None:
    output_paths = OutputPaths(tmp_path / "local.json", tmp_path / "share.json")
    github_client = ContextClient()
    talend_client = ContextClient()
    calls: list[tuple[str, dict[str, Any]]] = []

    monkeypatch.setattr(cli, "GitHubPublicClient", lambda: github_client)
    monkeypatch.setattr(cli, "_talend_client", lambda base_url: talend_client)

    def fake_github(*_: Any, **kwargs: Any) -> OutputPaths:
        calls.append(("github", kwargs))
        return output_paths

    def fake_talend(*_: Any, **kwargs: Any) -> OutputPaths:
        calls.append((str(kwargs["resource"]), kwargs))
        return output_paths

    monkeypatch.setattr(cli, "save_github_jobs", fake_github)
    monkeypatch.setattr(cli, "save_talend_inventory", fake_talend)

    commands = (
        [
            "github",
            "jobs",
            "owner/repository",
            "--path-prefix",
            "process/jobs",
        ],
        ["talend", "workspaces", "--environment-name", "Development"],
        ["talend", "tasks", "--workspace-id", "workspace-1"],
        ["talend", "runs", "--status", "executing", "--last-days", "2"],
    )
    for command in commands:
        result = runner.invoke(cli.app, command)
        assert result.exit_code == 0, result.output
    assert [name for name, _ in calls] == ["github", "workspaces", "tasks", "runs"]


def test_cli_redacts_expected_validation_failure() -> None:
    result = runner.invoke(cli.app, ["github", "jobs", "not-a-repository-slug"])
    assert result.exit_code == 2
    assert "OWNER/REPOSITORY" in result.output


def test_cli_redacts_local_io_failures(monkeypatch: Any) -> None:
    def fail_with_private_path(_: Path) -> OutputPaths:
        raise OSError("cannot write /private/customer/path")

    monkeypatch.setattr(cli, "save_demo", fail_with_private_path)
    result = runner.invoke(cli.app, ["demo"])

    assert result.exit_code == 2
    assert result.output.strip() == "Error: local_io_error"
    assert "/private/customer/path" not in result.output


def test_talend_client_factory_uses_explicit_or_environment_configuration(
    monkeypatch: Any,
) -> None:
    explicit = object()
    environment = object()
    monkeypatch.setattr(cli.TalendApiClient, "__new__", lambda *_: explicit)
    monkeypatch.setattr(cli.TalendApiClient, "from_env", lambda **_: environment)
    assert cli._talend_client("https://api.eu.cloud.talend.com") is explicit
    assert cli._talend_client(None) is environment


def test_module_entrypoint_invokes_app(monkeypatch: Any) -> None:
    called = 0

    def fake_app() -> None:
        nonlocal called
        called += 1

    monkeypatch.setattr(cli, "app", fake_app)
    runpy.run_module("talend_api_starter.__main__", run_name="__main__")
    assert called == 1


def test_module_entrypoint_is_side_effect_free_when_imported(monkeypatch: Any) -> None:
    def fail_app() -> None:
        raise AssertionError("normal module import must not start the CLI")

    monkeypatch.setattr(cli, "app", fail_app)
    runpy.run_module(
        "talend_api_starter.__main__",
        run_name="talend_api_starter.__main_import_test__",
    )
