"""Typer command surface for the safe starter."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import typer

from .errors import StarterError
from .github import GitHubPublicClient, parse_repository_slug
from .outputs import OutputPaths
from .talend_cloud import TALEND_BASE_URL_ENV, TalendCloudClient
from .workflows import save_cloud_inventory, save_demo, save_github_jobs

app = typer.Typer(
    no_args_is_help=True,
    help="Read-only Talend Cloud and public GitHub inventory starter.",
)
github_app = typer.Typer(no_args_is_help=True, help="Public GitHub operations.")
cloud_app = typer.Typer(no_args_is_help=True, help="GET-only Talend Cloud operations.")
app.add_typer(github_app, name="github")
app.add_typer(cloud_app, name="cloud")


def _run(action: Callable[[], OutputPaths]) -> None:
    try:
        paths = action()
    except StarterError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from None
    typer.echo(f"local_view: {paths.local_view}")
    typer.echo(f"share_safe: {paths.share_safe}")


def _cloud_client(base_url: str | None) -> TalendCloudClient:
    if base_url:
        return TalendCloudClient(base_url)
    return TalendCloudClient.from_env()


@app.command()
def demo(
    output_dir: Path = typer.Option(
        Path("demo-output"),
        "--output-dir",
        file_okay=False,
        help="Directory for local_view.json and share_safe.json.",
    ),
) -> None:
    """Run a network-free demo using clearly synthetic Talend XMI."""

    _run(lambda: save_demo(output_dir))


@github_app.command("jobs")
def github_jobs(
    repository: str = typer.Argument(
        ..., help="Public repository in OWNER/REPOSITORY format."
    ),
    ref: str = typer.Option("main", help="Branch or tag ref to pin."),
    path_prefix: str = typer.Option(
        "process", help="Repository-relative Talend process directory."
    ),
    output_dir: Path = typer.Option(
        Path("github-output"), "--output-dir", file_okay=False
    ),
) -> None:
    """Inventory .properties/.item pairs from one resolved commit."""

    def action() -> OutputPaths:
        owner, repository_name = parse_repository_slug(repository)
        with GitHubPublicClient() as client:
            return save_github_jobs(
                client,
                owner=owner,
                repository=repository_name,
                ref=ref,
                path_prefix=path_prefix,
                destination=output_dir,
            )

    _run(action)


@cloud_app.command("workspaces")
def cloud_workspaces(
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        envvar=TALEND_BASE_URL_ENV,
        help="Official Talend API base URL; or set TALEND_BASE_URL.",
    ),
    environment_name: str | None = typer.Option(None, help="Exact environment name."),
    output_dir: Path = typer.Option(
        Path("cloud-output/workspaces"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET a bounded page of Talend Cloud workspaces."""

    def action() -> OutputPaths:
        with _cloud_client(base_url) as client:
            return save_cloud_inventory(
                client,
                resource="workspaces",
                destination=output_dir,
                environment_name=environment_name,
            )

    _run(action)


@cloud_app.command("tasks")
def cloud_tasks(
    base_url: str | None = typer.Option(None, "--base-url", envvar=TALEND_BASE_URL_ENV),
    workspace_id: str | None = typer.Option(None, help="Optional workspace ID."),
    artifact_id: str | None = typer.Option(None, help="Optional artifact ID."),
    limit: int = typer.Option(100, min=1, max=100),
    offset: int = typer.Option(0, min=0, max=1_000),
    output_dir: Path = typer.Option(
        Path("cloud-output/tasks"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET a bounded page of Talend Cloud tasks."""

    def action() -> OutputPaths:
        with _cloud_client(base_url) as client:
            return save_cloud_inventory(
                client,
                resource="tasks",
                destination=output_dir,
                workspace_id=workspace_id,
                artifact_id=artifact_id,
                limit=limit,
                offset=offset,
            )

    _run(action)


@cloud_app.command("runs")
def cloud_runs(
    base_url: str | None = typer.Option(None, "--base-url", envvar=TALEND_BASE_URL_ENV),
    workspace_id: str | None = typer.Option(None, help="Optional workspace ID."),
    status: str | None = typer.Option(None, help="Optional documented run status."),
    last_days: int = typer.Option(7, min=1, max=10),
    limit: int = typer.Option(100, min=1, max=100),
    offset: int = typer.Option(0, min=0, max=1_000),
    output_dir: Path = typer.Option(
        Path("cloud-output/runs"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET bounded task-run history; this command never starts a run."""

    def action() -> OutputPaths:
        with _cloud_client(base_url) as client:
            return save_cloud_inventory(
                client,
                resource="runs",
                destination=output_dir,
                workspace_id=workspace_id,
                status=status,
                last_days=last_days,
                limit=limit,
                offset=offset,
            )

    _run(action)
