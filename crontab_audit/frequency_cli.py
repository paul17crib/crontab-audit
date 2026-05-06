"""CLI entry point for frequency classification reporting."""

import argparse
import sys
from typing import List

from crontab_audit.loader import load_from_file, load_from_directory
from crontab_audit.parser import CrontabEntry
from crontab_audit.frequency_report import (
    format_frequency_report,
    format_frequency_summary,
)


def _collect_entries(paths: List[str], is_dir: bool) -> List[CrontabEntry]:
    """Load entries from one or more files or a directory."""
    entries: List[CrontabEntry] = []
    if is_dir:
        for path in paths:
            from crontab_audit.loader import load_from_directory
            for hc in load_from_directory(path):
                entries.extend(hc.entries)
    else:
        for path in paths:
            hc = load_from_file(path)
            entries.extend(hc.entries)
    return entries


def cmd_report(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.paths, args.directory)
    if args.summary:
        print(format_frequency_summary(entries))
    else:
        print(format_frequency_report(entries, show_empty=args.show_empty))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-frequency",
        description="Report crontab entry frequency classifications.",
    )
    parser.add_argument(
        "paths", nargs="+", help="Crontab file(s) or director(ies) to analyse."
    )
    parser.add_argument(
        "-d", "--directory", action="store_true",
        help="Treat paths as directories of crontab files."
    )
    parser.add_argument(
        "-s", "--summary", action="store_true",
        help="Print a one-line frequency summary instead of full report."
    )
    parser.add_argument(
        "--show-empty", action="store_true",
        help="Include frequency buckets with zero entries."
    )
    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_report(args))


if __name__ == "__main__":  # pragma: no cover
    main()
