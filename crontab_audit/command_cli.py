"""CLI entry point for command statistics reporting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.command_report import (
    format_command_stats,
    format_top_commands,
    format_commands_per_host,
)
from crontab_audit.command_stats import build_command_stats


def _collect_entries(path: str):
    """Load crontab entries from a file or directory.

    Args:
        path: Path to a crontab file or a directory containing crontab files.

    Returns:
        A flat list of all CrontabEntry objects found.

    Raises:
        SystemExit: If the path does not exist.
    """
    p = Path(path)
    if not p.exists():
        print(f"error: path does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    hosts = []
    if p.is_dir():
        hosts = load_from_directory(str(p))
    else:
        hosts = [load_from_file(str(p))]
    entries = [e for h in hosts for e in h.entries]
    return entries


def cmd_top(args):
    entries = _collect_entries(args.path)
    print(format_top_commands(entries, n=args.n))


def cmd_all(args):
    entries = _collect_entries(args.path)
    stats = build_command_stats(entries)
    print(format_command_stats(stats))


def cmd_per_host(args):
    entries = _collect_entries(args.path)
    print(format_commands_per_host(entries))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-commands",
        description="Report command statistics from crontab files.",
    )
    parser.add_argument("path", help="Path to a crontab file or directory of crontabs")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_top = sub.add_parser("top", help="Show most frequent commands")
    p_top.add_argument("-n", type=int, default=10, help="Number of top commands")
    p_top.set_defaults(func=cmd_top)

    p_all = sub.add_parser("all", help="Show all command statistics")
    p_all.set_defaults(func=cmd_all)

    p_host = sub.add_parser("per-host", help="Show command counts per host")
    p_host.set_defaults(func=cmd_per_host)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
