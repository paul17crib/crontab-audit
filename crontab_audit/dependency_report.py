"""Formatting helpers for dependency checker output."""

from __future__ import annotations

from typing import List

from crontab_audit.dependency_checker import DependencyHint


def format_dependency_hints(hints: List[DependencyHint]) -> str:
    """Return a human-readable block listing all dependency hints."""
    if not hints:
        return "No inter-entry dependencies detected."
    lines = [f"Dependency hints ({len(hints)} found):", ""]
    for hint in hints:
        lines.append(f"  * {hint}")
    return "\n".join(lines)


def format_dependencies_by_token(hints: List[DependencyHint]) -> str:
    """Group and format dependency hints by shared token."""
    if not hints:
        return "No inter-entry dependencies detected."

    grouped: dict = {}
    for hint in hints:
        grouped.setdefault(hint.shared_token, []).append(hint)

    lines = []
    for token, group in sorted(grouped.items()):
        lines.append(f"Shared token: {token!r} ({group[0].reason})")
        for hint in group:
            lines.append(
                f"  [{hint.entry_a.host}] {hint.entry_a.command}"
            )
            lines.append(
                f"  [{hint.entry_b.host}] {hint.entry_b.command}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def format_dependency_summary(hints: List[DependencyHint]) -> str:
    """Return a one-line summary of dependency detection results."""
    if not hints:
        return "Dependencies: none detected."
    tokens = {h.shared_token for h in hints}
    return (
        f"Dependencies: {len(hints)} hint(s) across {len(tokens)} shared token(s)."
    )
