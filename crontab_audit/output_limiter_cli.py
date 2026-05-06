"""CLI wrapper for output_limiter — page/truncate/filter audit text output."""

import argparse
import sys
from typing import List

from crontab_audit.output_limiter import paginate, truncate, filter_lines


def _read_lines(path: str) -> List[str]:
    with open(path) as fh:
        return [line.rstrip("\n") for line in fh]


def cmd_page(args: argparse.Namespace) -> int:
    lines = _read_lines(args.file)
    result = paginate(lines, page=args.page, page_size=args.page_size)
    print(result)
    if result.has_next():
        print(f"(use --page {result.page + 1} to see the next page)")
    return 0


def cmd_truncate(args: argparse.Namespace) -> int:
    lines = _read_lines(args.file)
    output = truncate(lines, max_lines=args.max_lines)
    print("\n".join(output))
    return 0


def cmd_filter(args: argparse.Namespace) -> int:
    lines = _read_lines(args.file)
    matched = filter_lines(lines, keyword=args.keyword, case_sensitive=args.case_sensitive)
    if not matched:
        print(f"No lines matched '{args.keyword}'.")
        return 1
    print("\n".join(matched))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Limit/filter crontab audit output")
    sub = parser.add_subparsers(dest="command")

    p_page = sub.add_parser("page", help="Paginate output file")
    p_page.add_argument("file")
    p_page.add_argument("--page", type=int, default=1)
    p_page.add_argument("--page-size", type=int, default=50, dest="page_size")

    p_trunc = sub.add_parser("truncate", help="Truncate output file")
    p_trunc.add_argument("file")
    p_trunc.add_argument("--max-lines", type=int, default=100, dest="max_lines")

    p_filter = sub.add_parser("filter", help="Filter output lines by keyword")
    p_filter.add_argument("file")
    p_filter.add_argument("keyword")
    p_filter.add_argument("--case-sensitive", action="store_true", dest="case_sensitive")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"page": cmd_page, "truncate": cmd_truncate, "filter": cmd_filter}
    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
