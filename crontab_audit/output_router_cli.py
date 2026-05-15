"""CLI wrapper for the output-router feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from crontab_audit.loader import load_from_directory, load_from_file
from crontab_audit.formatter import format_all_hosts
from crontab_audit.output_router import build_routes_from_args, route_output


def _collect_text(paths: List[str], verbose: bool) -> str:
    """Load crontab files/directories and return formatted text."""
    hosts = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            hosts.extend(load_from_directory(str(path)))
        else:
            hosts.append(load_from_file(str(path)))
    return format_all_hosts(hosts, verbose=verbose)


def cmd_route(args: argparse.Namespace) -> int:
    text = _collect_text(args.paths, verbose=getattr(args, "verbose", False))
    routes = build_routes_from_args(
        output_file=getattr(args, "output", None),
        fmt=getattr(args, "format", "text"),
        append=getattr(args, "append", False),
        also_stdout=getattr(args, "also_stdout", False),
    )
    result = route_output(text, routes)
    if result.has_errors:
        for err in result.failed:
            print(f"[ERROR] {err}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Route crontab-audit output to one or more destinations."
    )
    p.add_argument("paths", nargs="+", help="Crontab files or directories")
    p.add_argument("-o", "--output", metavar="FILE", help="Write output to FILE")
    p.add_argument(
        "--format", choices=["text", "json", "csv"], default="text"
    )
    p.add_argument(
        "--append", action="store_true", help="Append to output file"
    )
    p.add_argument(
        "--also-stdout",
        action="store_true",
        help="Also print to stdout when --output is given",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return cmd_route(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
