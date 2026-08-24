"""Typer command surface for the read-only Talend API toolkit."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import typer

from ._version import __version__
from .errors import StarterError
from .github import GitHubPublicClient, parse_repository_slug
from .outputs import OutputPaths
from .talend_api import TALEND_BASE_URL_ENV, TalendApiClient
from .workflows import (
    save_demo,
    save_github_jobs,
    save_local_jobs,
    save_talend_inventory,
)

app = typer.Typer(
    no_args_is_help=True,
    help="Read-only Talend API, local Studio, and public GitHub CLI.",
)
local_app = typer.Typer(no_args_is_help=True, help="Local Talend Studio projects.")
github_app = typer.Typer(no_args_is_help=True, help="Public GitHub REST API.")
talend_app = typer.Typer(no_args_is_help=True, help="GET-only Talend APIs.")
app.add_typer(local_app, name="local")
app.add_typer(github_app, name="github")
app.add_typer(talend_app, name="talend")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed CLI version and exit.",
    ),
) -> None:
    """Use Talend APIs and inspect Talend Studio metadata safely."""


def _run(action: Callable[[], OutputPaths]) -> None:
    try:
        paths = action()
    except StarterError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from None
    except OSError:
        # Do not expose workstation paths or platform-specific diagnostics.
        typer.echo("Error: local_io_error", err=True)
        raise typer.Exit(code=2) from None
    typer.echo(f"local_view: {paths.local_view}")
    typer.echo(f"share_safe: {paths.share_safe}")


def _talend_client(base_url: str | None) -> TalendApiClient:
    if base_url:
        return TalendApiClient(base_url)
    return TalendApiClient.from_env()


@app.command()
def demo(
    output_dir: Path = typer.Option(
        Path("demo-output"),
        "--output-dir",
        file_okay=False,
        help="Directory for local_view.json and share_safe.json.",
    ),
) -> None:
    """Run a network-free demo using clearly synthetic Talend inputs."""

    _run(lambda: save_demo(output_dir))


@local_app.command("jobs")
def local_jobs(
    root: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=False,
        help="Local Talend Studio project root.",
    ),
    path_prefix: str = typer.Option(
        "process", help="Project-relative Talend process directory."
    ),
    output_dir: Path = typer.Option(
        Path("local-output"), "--output-dir", file_okay=False
    ),
) -> None:
    """Inventory local .properties/.item pairs without Git or network."""

    _run(
        lambda: save_local_jobs(
            root,
            path_prefix=path_prefix,
            destination=output_dir,
        )
    )


@github_app.command("jobs")
def github_jobs(
    repository: str = typer.Argument(
        ..., help="Public repository in OWNER/REPOSITORY format."
    ),
    ref: str = typer.Option(
        "main",
        help=(
            "Branch or tag to pin. Bare names try branch then tag; "
            "refs/heads/... and refs/tags/... are explicit."
        ),
    ),
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


@talend_app.command("workspaces")
def talend_workspaces(
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        envvar=TALEND_BASE_URL_ENV,
        help="Official Talend API base URL; or set TALEND_BASE_URL.",
    ),
    environment_name: str | None = typer.Option(None, help="Exact environment name."),
    output_dir: Path = typer.Option(
        Path("talend-output/workspaces"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET a bounded page of Talend workspaces."""

    def action() -> OutputPaths:
        with _talend_client(base_url) as client:
            return save_talend_inventory(
                client,
                resource="workspaces",
                destination=output_dir,
                environment_name=environment_name,
            )

    _run(action)


@talend_app.command("tasks")
def talend_tasks(
    base_url: str | None = typer.Option(None, "--base-url", envvar=TALEND_BASE_URL_ENV),
    workspace_id: str | None = typer.Option(None, help="Optional workspace ID."),
    artifact_id: str | None = typer.Option(None, help="Optional artifact ID."),
    limit: int = typer.Option(100, min=1, max=100),
    offset: int = typer.Option(0, min=0, max=1_000),
    output_dir: Path = typer.Option(
        Path("talend-output/tasks"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET a bounded page of Talend tasks."""

    def action() -> OutputPaths:
        with _talend_client(base_url) as client:
            return save_talend_inventory(
                client,
                resource="tasks",
                destination=output_dir,
                workspace_id=workspace_id,
                artifact_id=artifact_id,
                limit=limit,
                offset=offset,
            )

    _run(action)


@talend_app.command("runs")
def talend_runs(
    base_url: str | None = typer.Option(None, "--base-url", envvar=TALEND_BASE_URL_ENV),
    workspace_id: str | None = typer.Option(None, help="Optional workspace ID."),
    status: str | None = typer.Option(None, help="Optional documented run status."),
    last_days: int = typer.Option(7, min=1, max=10),
    limit: int = typer.Option(100, min=1, max=100),
    offset: int = typer.Option(0, min=0, max=1_000),
    output_dir: Path = typer.Option(
        Path("talend-output/runs"), "--output-dir", file_okay=False
    ),
) -> None:
    """GET bounded task-run history; this command never starts a run."""

    def action() -> OutputPaths:
        with _talend_client(base_url) as client:
            return save_talend_inventory(
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
