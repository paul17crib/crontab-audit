"""CLI for anomaly detection in crontab entries."""
import argparse
import sys
from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.anomaly_detector import detect_anomalies
from crontab_audit.anomaly_report import (
    format_anomaly_issues,
    format_anomalies_by_severity,
    format_anomaly_summary,
)


def _collect_entries(args):
    entries = []
    if args.dir:
        hosts = load_from_directory(args.dir)
        for host in hosts:
            entries.extend(host.entries)
    elif args.file:
        host = load_from_file(args.file)
        entries.extend(host.entries)
    return entries


def cmd_check(args) -> int:
    entries = _collect_entries(args)
    issues = detect_anomalies(entries)
    if args.by_severity:
        print(format_anomalies_by_severity(issues))
    else:
        print(format_anomaly_issues(issues))
    print()
    print(format_anomaly_summary(issues))
    return 1 if issues else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect anomalous crontab scheduling patterns."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to a single crontab file")
    source.add_argument("--dir", help="Directory of crontab files")
    parser.add_argument(
        "--by-severity",
        action="store_true",
        help="Group output by severity level",
    )
    parser.set_defaults(func=cmd_check)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
