"""CLI for the entry scorer module."""

import argparse
import sys
from typing import List

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.parser import CrontabEntry
from crontab_audit.entry_scorer import score_entries
from crontab_audit.entry_scorer_report import (
    format_score_report,
    format_score_summary,
    format_scores_by_grade,
)


def _collect_entries(args: argparse.Namespace) -> List[CrontabEntry]:
    entries: List[CrontabEntry] = []
    if args.dir:
        hosts = load_from_directory(args.dir)
        for h in hosts:
            entries.extend(h.entries)
    elif args.file:
        host = load_from_file(args.file)
        entries.extend(host.entries)
    return entries


def cmd_score(args: argparse.Namespace) -> int:
    entries = _collect_entries(args)
    if not entries:
        print("No entries found.")
        return 1

    scores = score_entries(entries)

    if args.summary:
        print(format_score_summary(scores))
    elif args.by_grade:
        print(format_scores_by_grade(scores))
    else:
        top_n = args.top if args.top else 0
        print(format_score_report(scores, top_n=top_n))
        print()
        print(format_score_summary(scores))

    worst = max(scores, key=lambda s: s.total_score)
    return 1 if worst.grade in ("D", "F") else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-scorer",
        description="Score crontab entries by risk, frequency, and complexity.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", metavar="PATH", help="Single crontab file")
    src.add_argument("--dir", metavar="DIR", help="Directory of crontab files")

    parser.add_argument("--top", type=int, default=0, metavar="N",
                        help="Show only top N worst entries")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary only")
    parser.add_argument("--by-grade", action="store_true",
                        help="Group output by grade")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_score(args))


if __name__ == "__main__":
    main()
