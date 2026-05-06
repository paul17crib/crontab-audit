"""CLI for user-based crontab audit reporting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.user_tracker import build_user_report
from crontab_audit.user_report_formatter import format_user_report, format_users_per_host


def _collect_entries(path: str):
    p = Path(path)
    if p.is_dir():
        hosts = load_from_directory(str(p))
    else:
        hosts = [load_from_file(str(p))]
    entries = []
    for host in hosts:
        entries.extend(host.entries)
    return entries


def cmd_report(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.path)
    report = build_user_report(entries)
    top_n = args.top if hasattr(args, "top") and args.top else 0
    print(format_user_report(report, top_n=top_n))
    return 0


def cmd_per_host(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.path)
    report = build_user_report(entries)
    print(format_users_per_host(report))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-user", description="User-based crontab audit reporting"
    )
    sub = parser.add_subparsers(dest="command")

    rep = sub.add_parser("report", help="Show per-user entry counts")
    rep.add_argument("path", help="Crontab file or directory")
    rep.add_argument("--top", type=int, default=0, help="Show only top N users")
    rep.set_defaults(func=cmd_report)

    per = sub.add_parser("per-host", help="Show users grouped by host")
    per.add_argument("path", help="Crontab file or directory")
    per.set_defaults(func=cmd_per_host)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
