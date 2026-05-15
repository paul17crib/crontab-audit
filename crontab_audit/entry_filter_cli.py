"""CLI for filtering crontab entries by various criteria."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.entry_filter import EntryFilter, apply_filter
from crontab_audit.entry_filter_report import format_filtered_entries, format_filter_summary


def _collect_entries(args: argparse.Namespace):
    path = Path(args.path)
    hosts = load_from_directory(path) if path.is_dir() else [load_from_file(path)]
    all_entries = [e for h in hosts for e in h.entries]
    return all_entries


def cmd_filter(args: argparse.Namespace) -> int:
    entries = _collect_entries(args)
    f = EntryFilter(
        host=args.host,
        user=args.user,
        command_pattern=args.command,
        minute=args.minute,
        hour=args.hour,
        tags=args.tag or [],
    )
    matched = apply_filter(entries, f)
    print(format_filtered_entries(matched, f))
    print()
    print(format_filter_summary(len(entries), len(matched)))
    return 0 if matched else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crontab-filter",
        description="Filter crontab entries by host, user, command, or schedule.",
    )
    p.add_argument("path", help="Path to a crontab file or directory of crontab files")
    p.add_argument("--host", default=None, help="Filter by hostname")
    p.add_argument("--user", default=None, help="Filter by username")
    p.add_argument("--command", default=None, help="Regex pattern to match against command")
    p.add_argument("--minute", default=None, help="Match entries with this minute field")
    p.add_argument("--hour", default=None, help="Match entries with this hour field")
    p.add_argument("--tag", action="append", help="Filter by tag (repeatable)")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return cmd_filter(args)


if __name__ == "__main__":
    sys.exit(main())
