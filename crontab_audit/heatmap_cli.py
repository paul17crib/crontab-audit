"""CLI subcommand: generate a schedule heatmap from crontab files."""

import argparse
import sys
from pathlib import Path
from crontab_audit.loader import load_from_file, load_from_directory
from crontab_audit.schedule_heatmap import build_heatmap, format_heatmap


def _collect_entries(paths: list):
    entries = []
    errors = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            hosts = load_from_directory(str(path))
        elif path.is_file():
            hosts = [load_from_file(str(path))]
        else:
            errors.append(f"Path not found: {p}")
            continue
        for host in hosts:
            entries.extend(host.entries)
            errors.extend(host.parse_errors)
    return entries, errors


def cmd_heatmap(args: argparse.Namespace) -> int:
    entries, errors = _collect_entries(args.paths)

    if errors and not args.quiet:
        print(f"[warn] {len(errors)} parse error(s) encountered.", file=sys.stderr)

    if not entries:
        print("No crontab entries found.", file=sys.stderr)
        return 1

    if args.host:
        entries = [e for e in entries if e.host == args.host]
        if not entries:
            print(f"No entries found for host: {args.host}", file=sys.stderr)
            return 1

    heatmap = build_heatmap(entries)

    if args.peaks:
        top = heatmap.peak_cells(top_n=args.peaks)
        print(f"Top {args.peaks} busiest time slots:")
        for cell in top:
            from crontab_audit.schedule_heatmap import WEEKDAY_NAMES
            day = WEEKDAY_NAMES[cell.weekday]
            print(f"  {day} {cell.hour:02d}:xx — {cell.count} job(s): {', '.join(cell.commands[:3])}")
    else:
        print(format_heatmap(heatmap))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crontab-heatmap",
        description="Visualise cron job frequency as a weekday/hour heatmap.",
    )
    parser.add_argument("paths", nargs="+", help="Crontab file(s) or directory.")
    parser.add_argument("--host", help="Filter to a specific hostname.")
    parser.add_argument(
        "--peaks", type=int, metavar="N",
        help="Show top N busiest time slots instead of full grid."
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress warnings.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_heatmap(args))


if __name__ == "__main__":
    main()
