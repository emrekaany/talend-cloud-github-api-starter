#!/usr/bin/env python3
"""Inspect one local Talend Studio project without Git or network access."""

from __future__ import annotations

import argparse
from pathlib import Path

from talend_api_starter.workflows import save_local_jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--path-prefix", default="process")
    parser.add_argument("--output-dir", type=Path, default=Path("local-output"))
    args = parser.parse_args()
    paths = save_local_jobs(
        args.root,
        path_prefix=args.path_prefix,
        destination=args.output_dir,
    )
    print(paths.local_view)
    print(paths.share_safe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
