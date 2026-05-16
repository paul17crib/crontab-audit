"""CLI for sorting and displaying crontab entries."""
from __future__ import annotations
import argparse
import sys
from typing import List
from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_sorter import sort_entries, available_sort_keys
from crontab_audit.entry_sorter_report import (
    format_sorted_entries,
    format_sort_summary,
    format_grouped_by_key,
)


def _collect_entries(paths: List[str]) -> List[CrontabEntry]:
    entries: List[CrontabEntry] = []
    for path in paths:
        import os
        if os.path.isdir(path):
            for hc in load_from_directory(path):
                entries.extend(hc.entries)
        else:
            hc = load_from_file(path)
            entries.extend(hc.entries)
    return entries


def cmd_sort(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.paths)
    if not entries:
        print("No entries found.", file=sys.stderr)
        return 1
    try:
        result = sort_entries(entries, key=args.key, reverse=args.reverse)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.group:
        print(format_grouped_by_key(result))
    elif args.summary:
        print(format_sort_summary(result))
    else:
        print(format_sorted_entries(result, max_rows=args.limit))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-sort",
        description="Sort crontab entries by various criteria.",
    )
    parser.add_argument("paths", nargs="+", help="Crontab files or directories")
    parser.add_argument(
        "--key",
        default="host",
        choices=available_sort_keys(),
        help="Sort key (default: host)",
    )
    parser.add_argument(
        "--reverse", action="store_true", help="Sort in descending order"
    )
    parser.add_argument(
        "--group", action="store_true", help="Group output by sort key"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print one-line summary only"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Max rows to display (0 = all)"
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_sort(args))


if __name__ == "__main__":
    main()
