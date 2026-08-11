#!/usr/bin/env python3
"""Regenerate the repository's intentionally fake Talend fixture pair."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from talend_api_starter.synthetic import write_synthetic_fixtures  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "examples" / "fixtures",
    )
    args = parser.parse_args()
    for path in write_synthetic_fixtures(args.output_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
