"""CLI helpers for baseline save/compare operations."""

import argparse
import sys
from typing import List

from crontab_audit.loader import load_from_directory, HostCrontab
from crontab_audit.baseline import compare_against_baseline, save_baseline


def _load_hosts(directory: str) -> List[HostCrontab]:
    hosts = load_from_directory(directory)
    if not hosts:
        print(f"No crontab files found in: {directory}", file=sys.stderr)
        sys.exit(1)
    return hosts


def cmd_save(args: argparse.Namespace) -> int:
    """Save current crontab state as the new baseline."""
    hosts = _load_hosts(args.directory)
    save_baseline(hosts, args.baseline)
    print(f"Baseline saved to {args.baseline} ({len(hosts)} host(s)).")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare current crontab state against saved baseline."""
    hosts = _load_hosts(args.directory)
    report = compare_against_baseline(hosts, args.baseline)

    if report is None:
        print("No baseline found. Run 'baseline save' first.")
        return 1

    print(report.summary())
    return 1 if report.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-baseline",
        description="Save and compare crontab baselines.",
    )
    parser.add_argument(
        "--directory", "-d", required=True,
        help="Directory containing per-host crontab files.",
    )
    parser.add_argument(
        "--baseline", "-b", default="baseline.json",
        help="Path to the baseline snapshot file (default: baseline.json).",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("save", help="Save current state as baseline.")
    subparsers.add_parser("compare", help="Compare current state against baseline.")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        return cmd_save(args)
    elif args.command == "compare":
        return cmd_compare(args)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
