"""CLI commands for managing and applying the crontab whitelist."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.whitelist import Whitelist, WhitelistEntry, load_whitelist, save_whitelist
from crontab_audit.whitelist_report import (
    format_whitelist_entries,
    format_whitelist_summary,
    format_whitelisted_entries,
)


def _collect_entries(args: argparse.Namespace):
    if Path(args.input).is_dir():
        hosts = load_from_directory(args.input)
    else:
        hosts = [load_from_file(args.input)]
    return [e for h in hosts for e in h.entries]


def cmd_list(args: argparse.Namespace) -> int:
    wl = load_whitelist(args.whitelist) if Path(args.whitelist).exists() else Whitelist()
    print(format_whitelist_entries(wl.entries))
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    entries = _collect_entries(args)
    wl = load_whitelist(args.whitelist) if Path(args.whitelist).exists() else Whitelist()
    suppressed = sum(1 for e in entries if wl.is_whitelisted(e))
    print(format_whitelisted_entries(entries, wl))
    print()
    print(format_whitelist_summary(len(entries), suppressed))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    wl = load_whitelist(args.whitelist) if Path(args.whitelist).exists() else Whitelist()
    entry = WhitelistEntry(
        command_contains=args.command or "",
        schedule_exact=args.schedule or "",
        host=args.host or "",
        reason=args.reason or "",
    )
    wl.entries.append(entry)
    save_whitelist(wl, args.whitelist)
    print(f"Added whitelist entry. Total: {len(wl.entries)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crontab-whitelist", description="Manage crontab whitelist")
    p.add_argument("--whitelist", default="whitelist.json", help="Path to whitelist JSON")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List whitelist entries")

    ap = sub.add_parser("apply", help="Show which entries are suppressed")
    ap.add_argument("input", help="Crontab file or directory")

    add = sub.add_parser("add", help="Add a whitelist entry")
    add.add_argument("--command", help="Substring to match in command")
    add.add_argument("--schedule", help="Exact schedule string to match")
    add.add_argument("--host", help="Hostname to scope the rule")
    add.add_argument("--reason", help="Human-readable reason")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"list": cmd_list, "apply": cmd_apply, "add": cmd_add}
    fn = dispatch.get(args.cmd)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
