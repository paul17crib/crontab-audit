"""Formatting helpers for output-router diagnostics."""
from __future__ import annotations

from typing import List

from crontab_audit.output_router import OutputRoute, RoutingResult


def format_route_list(routes: List[OutputRoute]) -> str:
    """Return a human-readable summary of configured routes."""
    if not routes:
        return "No output routes configured."
    lines = ["Configured output routes:"]
    for i, r in enumerate(routes, 1):
        mode = "append" if r.append else "overwrite"
        lines.append(f"  {i}. dest={r.dest!r}  format={r.fmt}  mode={mode}")
    return "\n".join(lines)


def format_routing_result(result: RoutingResult) -> str:
    """Return a concise summary of a routing operation's outcome."""
    lines: List[str] = []
    if result.succeeded:
        lines.append("Successfully written to:")
        for dest in result.succeeded:
            lines.append(f"  ✓ {dest}")
    if result.failed:
        lines.append("Failed to write to:")
        for err in result.failed:
            lines.append(f"  ✗ {err}")
    if not lines:
        return "No routes were attempted."
    return "\n".join(lines)


def format_routing_summary(routes: List[OutputRoute], result: RoutingResult) -> str:
    """Combine route list and result into a single report block."""
    parts = [
        format_route_list(routes),
        "",
        format_routing_result(result),
    ]
    if result.has_errors:
        parts.append("\n[WARNING] One or more output destinations failed.")
    return "\n".join(parts)
