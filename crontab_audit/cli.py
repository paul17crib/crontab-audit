"""Command-line interface for crontab-audit."""

import argparse
import sys
from pathlib import Path
from typing import List

from crontab_audit.parser import parse_line, CrontabParseError
from crontab_audit.validator import validate_entry, ValidationError
from crontab_audit.reporter import build_report


def load_entries_from_file(path: Path):
    entries = []
    errors = []
    with path.open() as fh:
        for lineno, raw in enumerate(fh, start=1):
            try:
                entry = parse_line(raw)
                if entry is None:
                    continue
                validate_entry(entry)
                entries.append(entry)
            except (CrontabParseError, ValidationError) as exc:
                errors.append(f"  Line {lineno}: {exc}")
    return entries, errors


def run(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crontab-audit",
        description="Parse and audit crontab files for risky or overlapping schedules.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Crontab file(s) to audit. Use --host to label each file.",
    )
    parser.add_argument(
        "--host",
        metavar="NAME",
        help="Host label (defaults to filename).",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if any issues are found.",
    )
    args = parser.parse_args(argv)

    exit_code = 0
    for filepath in args.files:
        path = Path(filepath)
        host = args.host or path.name
        if not path.exists():
            print(f"ERROR: File not found: {filepath}", file=sys.stderr)
            exit_code = 2
            continue

        entries, parse_errors = load_entries_from_file(path)
        if parse_errors:
            print(f"Parse/validation errors in {filepath}:")
            for err in parse_errors:
                print(err)

        report = build_report(host, entries)
        print(report.detailed())
        print()

        if args.fail_on_issues and report.has_issues():
            exit_code = 1

    return exit_code


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
