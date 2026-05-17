"""CLI for grouping crontab entries."""

import argparse
import sys
from typing import List

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_grouper import group_entries
from crontab_audit.entry_grouper_report import format_groups, format_group_summary


def _collect_entries(path: str, is_dir: bool) -> List[CrontabEntry]:
    if is_dir:
        hosts = load_from_directory(path)
    else:
        hosts = [load_from_file(path)]
    entries: List[CrontabEntry] = []
    for host in hosts:
        entries.extend(host.entries)
    return entries


def cmd_group(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.path, args.dir)
    if not entries:
        print("No entries found.")
        return 0
    groups = group_entries(entries, by=args.by)
    if args.summary:
        print(format_group_summary(groups))
    else:
        print(format_groups(groups, verbose=args.verbose))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-grouper",
        description="Group crontab entries by a chosen key.",
    )
    parser.add_argument("path", help="Path to crontab file or directory.")
    parser.add_argument("--dir", action="store_true", help="Treat path as a directory.")
    parser.add_argument(
        "--by",
        choices=["host", "user", "frequency", "hour"],
        default="host",
        help="Grouping key (default: host).",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show entry details.")
    parser.add_argument("--summary", "-s", action="store_true", help="Show summary only.")
    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_group(args))
