#!/usr/bin/env python3
"""Small Talend Cloud example; PAT and region come from the environment."""

from __future__ import annotations

import argparse
from pathlib import Path

from talend_api_starter.talend_cloud import TalendCloudClient
from talend_api_starter.workflows import save_cloud_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("resource", choices=("workspaces", "tasks", "runs"))
    parser.add_argument("--workspace-id")
    parser.add_argument("--output-dir", type=Path, default=Path("cloud-output"))
    args = parser.parse_args()
    with TalendCloudClient.from_env() as client:
        paths = save_cloud_inventory(
            client,
            resource=args.resource,
            workspace_id=args.workspace_id,
            destination=args.output_dir / args.resource,
        )
    print(paths.local_view)
    print(paths.share_safe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
