"""Reusable workflows shared by the Typer CLI and Python examples."""

from __future__ import annotations

from pathlib import Path

from .github import GitHubPublicClient
from .outputs import (
    OutputPaths,
    cloud_outputs,
    github_job_outputs,
    synthetic_demo_outputs,
    write_output_bundle,
)
from .synthetic import SYNTHETIC_CLOUD_METADATA, synthetic_files
from .talend_cloud import TalendCloudClient
from .xmlsafe import inventory_talend_jobs


def save_demo(destination: Path) -> OutputPaths:
    """Run a deterministic offline flow over synthetic files only."""

    inventory = inventory_talend_jobs(synthetic_files())
    local_view, share_safe = synthetic_demo_outputs(inventory, SYNTHETIC_CLOUD_METADATA)
    return write_output_bundle(destination, local_view, share_safe)


def save_github_jobs(
    client: GitHubPublicClient,
    *,
    owner: str,
    repository: str,
    ref: str,
    path_prefix: str,
    destination: Path,
) -> OutputPaths:
    snapshot = client.fetch_job_files(
        owner, repository, ref=ref, path_prefix=path_prefix
    )
    inventory = inventory_talend_jobs(snapshot.files)
    local_view, share_safe = github_job_outputs(snapshot, inventory)
    return write_output_bundle(destination, local_view, share_safe)


def save_cloud_inventory(
    client: TalendCloudClient,
    *,
    resource: str,
    destination: Path,
    workspace_id: str | None = None,
    artifact_id: str | None = None,
    environment_name: str | None = None,
    status: str | None = None,
    last_days: int = 7,
    limit: int = 100,
    offset: int = 0,
) -> OutputPaths:
    if resource == "workspaces":
        payload = client.list_workspaces(environment_name=environment_name)
    elif resource == "tasks":
        payload = client.list_tasks(
            workspace_id=workspace_id,
            artifact_id=artifact_id,
            limit=limit,
            offset=offset,
        )
    elif resource == "runs":
        payload = client.list_runs(
            workspace_id=workspace_id,
            status=status,
            last_days=last_days,
            limit=limit,
            offset=offset,
        )
    else:
        raise ValueError("Unsupported cloud resource")
    local_view, share_safe = cloud_outputs(
        region=client.region,
        resource=resource,
        payload=payload,
        secrets=client.redaction_secrets,
    )
    return write_output_bundle(destination, local_view, share_safe)
