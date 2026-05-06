"""CLI sub-command: audit crontabs against time windows."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.parser import CrontabEntry
from crontab_audit.time_window import (
    OFFICE_HOURS, OFF_HOURS, WEEKEND,
    TimeWindow, find_window_matches, filter_by_window,
)
from crontab_audit.time_window_report import (
    format_window_matches, format_window_summary, format_off_hours_warnings,
)

_BUILTIN_WINDOWS = {
    "office-hours": OFFICE_HOURS,
    "off-hours": OFF_HOURS,
    "weekend": WEEKEND,
}


def _collect_entries(path: str) -> List[CrontabEntry]:
    p = Path(path)
    if p.is_dir():
        hosts = load_from_directory(str(p))
    else:
        hosts = [load_from_file(str(p))]
    return [e for h in hosts for e in h.entries]


def cmd_check(args: argparse.Namespace) -> int:
    entries = _collect_entries(args.path)
    windows: List[TimeWindow] = [_BUILTIN_WINDOWS[w] for w in args.windows]
    matches = find_window_matches(entries, windows)

    if args.summary:
        print(format_window_summary(matches))
    elif args.off_hours_only:
        print(format_off_hours_warnings(matches))
    else:
        print(format_window_matches(matches))

    return 1 if matches else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crontab-time-window",
        description="Check crontab entries against time windows.",
    )
    p.add_argument("path", help="Crontab file or directory of crontab files")
    p.add_argument(
        "--windows",
        nargs="+",
        choices=list(_BUILTIN_WINDOWS),
        default=list(_BUILTIN_WINDOWS),
        help="Windows to check against (default: all)",
    )
    p.add_argument("--summary", action="store_true", help="Show count summary only")
    p.add_argument("--off-hours-only", dest="off_hours_only", action="store_true")
    return p


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_check(args))


if __name__ == "__main__":  # pragma: no cover
    main()
