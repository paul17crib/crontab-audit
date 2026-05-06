"""CLI entry-point for the retention policy checker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.retention import find_retention_issues
from crontab_audit.retention_report import (
    format_retention_by_host,
    format_retention_issues,
    format_retention_summary,
)


def _collect_entries(path: str):
    p = Path(path)
    if p.is_dir():
        hosts = load_from_directory(str(p))
    else:
        hosts = [load_from_file(str(p))]
    entries = []
    for h in hosts:
        entries.extend(h.entries)
    return entries


def cmd_check(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.path)
    issues = find_retention_issues(entries)

    if args.by_host:
        print(format_retention_by_host(issues))
    elif args.summary:
        print(format_retention_summary(issues))
    else:
        print(format_retention_issues(issues))

    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-retention",
        description="Check crontab entries for missing data-retention policies.",
    )
    parser.add_argument(
        "path", help="Path to a crontab file or directory of crontab files."
    )
    parser.add_argument(
        "--by-host", action="store_true", help="Group output by host."
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print a one-line summary."
    )
    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_check(args))


if __name__ == "__main__":  # pragma: no cover
    main()
