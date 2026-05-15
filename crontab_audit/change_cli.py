"""CLI for comparing current crontab state against a saved snapshot."""
import argparse
import sys
from crontab_audit.loader import load_from_directory
from crontab_audit.snapshot import save_snapshot, load_snapshot
from crontab_audit.change_tracker import track_changes
from crontab_audit.change_report_formatter import format_change_report, format_changes_by_host


def _load_hosts(directory: str):
    return load_from_directory(directory)


def cmd_save(args) -> int:
    hosts = _load_hosts(args.directory)
    save_snapshot(hosts, args.snapshot)
    print(f"Snapshot saved to {args.snapshot} ({len(hosts)} hosts).")
    return 0


def cmd_compare(args) -> int:
    current_hosts = _load_hosts(args.directory)
    try:
        old_hosts = load_snapshot(args.snapshot)
    except FileNotFoundError:
        print(f"Snapshot not found: {args.snapshot}", file=sys.stderr)
        return 2

    report = track_changes(old_hosts, current_hosts)

    if args.by_host:
        print(format_changes_by_host(report))
    else:
        print(format_change_report(report))

    return 1 if report.has_changes else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track crontab changes over time")
    sub = parser.add_subparsers(dest="command")

    save_p = sub.add_parser("save", help="Save current state as snapshot")
    save_p.add_argument("directory", help="Directory containing crontab files")
    save_p.add_argument("snapshot", help="Path to write snapshot JSON")

    cmp_p = sub.add_parser("compare", help="Compare current state to snapshot")
    cmp_p.add_argument("directory", help="Directory containing crontab files")
    cmp_p.add_argument("snapshot", help="Path to snapshot JSON")
    cmp_p.add_argument("--by-host", action="store_true", help="Group output by host")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "save":
        sys.exit(cmd_save(args))
    elif args.command == "compare":
        sys.exit(cmd_compare(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
