"""CLI entry point for permission checks."""

import argparse
import sys
from pathlib import Path
from crontab_audit.loader import load_from_file, load_from_directory
from crontab_audit.permission_checker import check_permissions
from crontab_audit.permission_report import (
    format_permission_issues,
    format_permission_by_severity,
    format_permission_summary,
)


def _collect_entries(args):
    entries = []
    if args.dir:
        hosts = load_from_directory(args.dir)
        for h in hosts:
            entries.extend(h.entries)
    elif args.file:
        host = load_from_file(args.file)
        entries.extend(host.entries)
    return entries


def cmd_check(args) -> int:
    entries = _collect_entries(args)
    issues = check_permissions(entries)

    if args.severity:
        issues = [i for i in issues if i.severity == args.severity]

    if args.by_severity:
        print(format_permission_by_severity(issues))
    else:
        print(format_permission_issues(issues))

    if args.summary:
        print()
        print(format_permission_summary(issues))

    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check crontab entries for permission risks."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Path to a single crontab file")
    src.add_argument("--dir", help="Directory containing crontab files")
    parser.add_argument(
        "--severity",
        choices=["critical", "warning", "info"],
        help="Filter by severity level",
    )
    parser.add_argument(
        "--by-severity", action="store_true", help="Group output by severity"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print summary after results"
    )
    parser.set_defaults(func=cmd_check)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
