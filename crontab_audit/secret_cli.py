"""CLI entry point for the secret scanner."""
from __future__ import annotations
import argparse
import sys
from typing import List

from crontab_audit.loader import load_from_file, load_from_directory
from crontab_audit.parser import CrontabEntry
from crontab_audit.secret_scanner import scan_entries
from crontab_audit.secret_report import (
    format_secret_issues,
    format_secrets_by_host,
    format_secret_summary,
)


def _collect_entries(args: argparse.Namespace) -> List[CrontabEntry]:
    entries: List[CrontabEntry] = []
    if args.dir:
        hosts = load_from_directory(args.dir)
        for hc in hosts:
            entries.extend(hc.entries)
    elif args.file:
        hc = load_from_file(args.file)
        entries.extend(hc.entries)
    return entries


def cmd_check(args: argparse.Namespace) -> int:
    entries = _collect_entries(args)
    issues = scan_entries(entries)
    if args.by_host:
        print(format_secrets_by_host(issues))
    elif args.summary:
        print(format_secret_summary(issues))
    else:
        print(format_secret_issues(issues))
    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-secrets",
        description="Scan crontab entries for hardcoded secrets.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", metavar="PATH", help="Single crontab file")
    src.add_argument("--dir", metavar="PATH", help="Directory of crontab files")
    parser.add_argument("--by-host", action="store_true", help="Group output by host")
    parser.add_argument("--summary", action="store_true", help="Print summary only")
    parser.set_defaults(func=cmd_check)
    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
