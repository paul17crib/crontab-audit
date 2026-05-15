"""Routes audit output to file, stdout, or multiple destinations."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, List, Optional


@dataclass
class OutputRoute:
    """Describes a single output destination."""
    dest: str  # 'stdout', 'stderr', or a file path
    fmt: str = "text"  # 'text', 'json', 'csv'
    append: bool = False

    def __str__(self) -> str:
        mode = "append" if self.append else "write"
        return f"OutputRoute(dest={self.dest!r}, fmt={self.fmt!r}, mode={mode})"


@dataclass
class RoutingResult:
    """Collects success/failure info after routing."""
    succeeded: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.failed)

    def __str__(self) -> str:
        return (
            f"RoutingResult(ok={len(self.succeeded)}, failed={len(self.failed)})"
        )


def _open_dest(route: OutputRoute) -> IO[str]:
    """Return an open file-like object for the given route destination."""
    if route.dest == "stdout":
        return sys.stdout
    if route.dest == "stderr":
        return sys.stderr
    mode = "a" if route.append else "w"
    return open(route.dest, mode, encoding="utf-8")  # noqa: WPS515


def route_output(content: str, routes: List[OutputRoute]) -> RoutingResult:
    """Write *content* to every route, collecting outcomes."""
    result = RoutingResult()
    for route in routes:
        try:
            fh = _open_dest(route)
            try:
                fh.write(content)
                if not content.endswith("\n"):
                    fh.write("\n")
            finally:
                if route.dest not in ("stdout", "stderr"):
                    fh.close()
            result.succeeded.append(route.dest)
        except OSError as exc:  # pragma: no cover
            result.failed.append(f"{route.dest}: {exc}")
    return result


def build_routes_from_args(
    output_file: Optional[str],
    fmt: str = "text",
    append: bool = False,
    also_stdout: bool = False,
) -> List[OutputRoute]:
    """Construct a list of routes from CLI-style arguments."""
    routes: List[OutputRoute] = []
    if output_file:
        routes.append(OutputRoute(dest=output_file, fmt=fmt, append=append))
        if also_stdout:
            routes.append(OutputRoute(dest="stdout", fmt=fmt))
    else:
        routes.append(OutputRoute(dest="stdout", fmt=fmt))
    return routes
