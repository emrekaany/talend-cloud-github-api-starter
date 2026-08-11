from __future__ import annotations

import importlib.util
import json
import os
import stat
from pathlib import Path

import pytest
from typer.testing import CliRunner

from talend_api_starter.cli import app
from talend_api_starter.errors import ValidationError
from talend_api_starter.github import GitHubSnapshot
from talend_api_starter.outputs import (
    cloud_outputs,
    github_job_outputs,
    write_output_bundle,
)
from talend_api_starter.synthetic import synthetic_files
from talend_api_starter.workflows import save_demo
from talend_api_starter.xmlsafe import inventory_talend_jobs

runner = CliRunner()


def test_demo_is_offline_and_writes_two_output_classes(tmp_path: Path) -> None:
    paths = save_demo(tmp_path)
    local = json.loads(paths.local_view.read_text(encoding="utf-8"))
    share = json.loads(paths.share_safe.read_text(encoding="utf-8"))

    assert local["output_class"] == "local_view"
    assert share["output_class"] == "share_safe"
    assert local["source"] == {"provider": "offline_synthetic_fixture"}
    assert local["jobs"][0]["properties_path"].startswith("process/demo/")
    assert local["cloud_metadata"]["tasks"][0]["name"] == "Synthetic Customer Load"
    assert share["studio_aggregates"]["job_count"] == 1
    assert share["studio_aggregates"] == {"component_count": 2, "job_count": 1}
    assert share["cloud_aggregates"]["runs"]["record_count"] == 1
    assert "properties_path" not in json.dumps(share)
    assert "SyntheticCustomers" not in json.dumps(share)
    assert "Synthetic Customer Load" not in json.dumps(share)
    assert "unique_name" not in json.dumps(share)
    if os.name != "nt":
        assert stat.S_IMODE(paths.local_view.stat().st_mode) == 0o600
        assert stat.S_IMODE(paths.share_safe.stat().st_mode) == 0o644


def test_typer_demo_command(tmp_path: Path) -> None:
    output = tmp_path / "cli-demo"
    result = runner.invoke(app, ["demo", "--output-dir", str(output)])
    assert result.exit_code == 0, result.output
    assert (output / "local_view.json").is_file()
    assert (output / "share_safe.json").is_file()


@pytest.mark.skipif(os.name == "nt", reason="Windows symlinks may require privileges")
def test_output_destination_rejects_directory_symlink(tmp_path: Path) -> None:
    real_directory = tmp_path / "real"
    real_directory.mkdir()
    linked_directory = tmp_path / "linked"
    linked_directory.symlink_to(real_directory, target_is_directory=True)
    with pytest.raises(ValidationError, match="real directory"):
        write_output_bundle(linked_directory, {"local": 1}, {"share": 1})


@pytest.mark.skipif(os.name == "nt", reason="POSIX directory modes only")
def test_output_destination_rejects_group_world_writable_directory(
    tmp_path: Path,
) -> None:
    unsafe_directory = tmp_path / "unsafe"
    unsafe_directory.mkdir(mode=0o700)
    unsafe_directory.chmod(0o777)
    try:
        with pytest.raises(ValidationError, match="group/world writable"):
            write_output_bundle(unsafe_directory, {"local": 1}, {"share": 1})
    finally:
        unsafe_directory.chmod(0o700)


@pytest.mark.skipif(os.name == "nt", reason="POSIX parent directory modes only")
def test_output_destination_rejects_untrusted_writable_parent(tmp_path: Path) -> None:
    unsafe_parent = tmp_path / "unsafe-parent"
    unsafe_parent.mkdir(mode=0o700)
    unsafe_parent.chmod(0o777)
    try:
        with pytest.raises(ValidationError, match="parent directory"):
            write_output_bundle(unsafe_parent / "output", {"local": 1}, {"share": 1})
    finally:
        unsafe_parent.chmod(0o700)


def test_nested_command_names_are_exposed() -> None:
    commands = (
        ["github", "jobs", "--help"],
        ["cloud", "workspaces", "--help"],
        ["cloud", "tasks", "--help"],
        ["cloud", "runs", "--help"],
    )
    for args in commands:
        result = runner.invoke(app, list(args))
        assert result.exit_code == 0, result.output
    github_help = runner.invoke(app, ["github", "jobs", "--help"])
    assert "OWNER/REPOSITORY" in github_help.output


def test_cloud_output_redacts_secret_and_allowlists_share_fields() -> None:
    secret = "talend_pat_super_secret"
    payload = {
        "items": [
            {
                "executionId": "private-id",
                "userId": "private-user",
                "status": "execution_successful",
                "executionType": "SCHEDULED",
                "executionDestination": "REMOTE_ENGINE",
                "startTimestamp": "2026-08-11T10:00:00Z",
                "finishTimestamp": "2026-08-11T10:00:01Z",
                "numberOfProcessedRows": 999,
                "numberOfRejectedRows": 3,
                "name": "private-task-name",
                "description": "private-description",
                "message": f"upstream echoed {secret}",
                "accessToken": secret,
            }
        ],
        secret: "secret echoed as a JSON key",
    }
    local, share = cloud_outputs(
        region="eu", resource="runs", payload=payload, secrets=(secret,)
    )
    assert secret not in json.dumps(local)
    assert local["response"]["items"][0]["accessToken"] == "[REDACTED]"
    assert share["aggregates"]["status_counts"] == {"execution_successful": 1}
    assert share["aggregates"]["execution_type_counts"] == {"SCHEDULED": 1}
    assert "duration_ms" not in share["aggregates"]
    assert "startTimestamp" not in json.dumps(share)
    assert "finishTimestamp" not in json.dumps(share)
    assert "private-id" not in json.dumps(share)
    assert "private-user" not in json.dumps(share)
    assert "private-task-name" not in json.dumps(share)
    assert "private-description" not in json.dumps(share)
    assert "numberOfProcessedRows" not in json.dumps(share)
    assert "numberOfRejectedRows" not in json.dumps(share)
    assert share["source"] == {
        "provider": "talend_cloud_api",
        "resource": "runs",
    }
    assert "region" not in share["source"]


def test_unknown_cloud_enums_are_bucketed_without_identity_leak() -> None:
    identity = "customer-secret-status"
    _, share = cloud_outputs(
        region="private-region",
        resource="runs",
        payload={
            "items": [
                {
                    "status": identity,
                    "executionStatus": identity,
                    "executionType": identity,
                    "executionDestination": identity,
                }
            ]
        },
    )
    rendered = json.dumps(share)
    assert identity not in rendered
    assert "private-region" not in rendered
    assert share["aggregates"] == {
        "execution_destination_counts": {"other": 1},
        "execution_status_counts": {"other": 1},
        "execution_type_counts": {"other": 1},
        "record_count": 1,
        "status_counts": {"other": 1},
    }


@pytest.mark.parametrize("resource", ["workspaces", "tasks"])
def test_workspace_and_task_share_safe_are_count_only(resource: str) -> None:
    identity = "private-name-or-status"
    _, share = cloud_outputs(
        region="private-region",
        resource=resource,
        payload={"items": [{"id": identity, "name": identity, "status": identity}]},
    )
    assert share["aggregates"] == {"record_count": 1}
    assert identity not in json.dumps(share)


def test_output_temp_file_is_removed_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed_modes: list[int] = []

    def fail_replace(source: Path, _: Path) -> None:
        observed_modes.append(stat.S_IMODE(source.stat().st_mode))
        raise OSError("synthetic replace failure")

    monkeypatch.setattr("talend_api_starter.outputs.os.replace", fail_replace)
    with pytest.raises(OSError, match="synthetic replace failure"):
        write_output_bundle(
            tmp_path,
            {"output_class": "local_view"},
            {"output_class": "share_safe"},
        )
    assert len(observed_modes) == 1
    if os.name != "nt":
        assert observed_modes == [0o600]
    assert list(tmp_path.glob(".*.tmp")) == []


def test_github_share_safe_excludes_source_and_job_identity() -> None:
    inventory = inventory_talend_jobs(synthetic_files())
    snapshot = GitHubSnapshot(
        owner="private-owner",
        repository="private-repository",
        ref="heads/main",
        commit_sha="a" * 40,
        root_tree_sha="b" * 40,
        prefix_tree_sha="c" * 40,
        path_prefix="process/demo",
        files=synthetic_files(),
    )
    _, share = github_job_outputs(snapshot, inventory)
    rendered = json.dumps(share)
    for forbidden in (
        "private-owner",
        "private-repository",
        "SyntheticCustomers",
        "process/demo",
        "a" * 40,
    ):
        assert forbidden not in rendered
    assert share["aggregates"]["job_count"] == 1


def test_beginner_examples_import_without_running_network() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    for name in ("github_inventory.py", "talend_cloud_inventory.py"):
        path = repository_root / "examples" / "python" / name
        spec = importlib.util.spec_from_file_location(f"example_{name}", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert callable(module.main)
