"""CLI entry point for the resource contention checker."""
from __future__ import annotations
import argparse
import sys
from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.resource_monitor import check_resource_risk
from crontab_audit.resource_report import (
    format_resource_issues,
    format_resource_by_severity,
    format_resource_summary,
)


def _collect_entries(args: argparse.Namespace):
    entries = []
    if args.dir:
        hosts = load_from_directory(args.dir)
    else:
        hosts = [load_from_file(args.file)]
    for host in hosts:
        entries.extend(host.entries)
    return entries


def cmd_check(args: argparse.Namespace) -> int:
    entries = _collect_entries(args)
    issues = check_resource_risk(entries)

    if args.severity:
        issues = [i for i in issues if i.severity == args.severity]

    if args.grouped:
        print(format_resource_by_severity(issues))
    else:
        print(format_resource_issues(issues))

    print()
    print(format_resource_summary(issues))
    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check crontab entries for resource contention risks."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to a single crontab file")
    source.add_argument("--dir", help="Directory of crontab files")
    parser.add_argument(
        "--severity",
        choices=["high", "medium", "low"],
        help="Filter output to a specific severity level",
    )
    parser.add_argument(
        "--grouped",
        action="store_true",
        help="Group output by severity",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_check(args))


if __name__ == "__main__":
    main()
