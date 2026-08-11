#!/usr/bin/env python3
"""Small public-repository example built on the package workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from talend_api_starter.github import GitHubPublicClient, parse_repository_slug
from talend_api_starter.workflows import save_github_jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="OWNER/REPOSITORY")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--path-prefix", default="process")
    parser.add_argument("--output-dir", type=Path, default=Path("github-output"))
    args = parser.parse_args()
    owner, repository = parse_repository_slug(args.repository)
    with GitHubPublicClient() as client:
        paths = save_github_jobs(
            client,
            owner=owner,
            repository=repository,
            ref=args.ref,
            path_prefix=args.path_prefix,
            destination=args.output_dir,
        )
    print(paths.local_view)
    print(paths.share_safe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
