"""Unified output formatter supporting text, JSON, and CSV output modes."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Literal, Optional

OutputMode = Literal["text", "json", "csv"]


def _to_serializable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serialisable types."""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    # Fallback: use __str__
    return str(obj)


def format_as_text(rows: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """Render a list of dicts as a plain-text table."""
    lines: List[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    if not rows:
        lines.append("(no results)")
        return "\n".join(lines)
    headers = list(rows[0].keys())
    col_widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))
    header_line = "  ".join(h.ljust(col_widths[h]) for h in headers)
    lines.append(header_line)
    lines.append("  ".join("-" * col_widths[h] for h in headers))
    for row in rows:
        lines.append("  ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers))
    return "\n".join(lines)


def format_as_json(rows: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """Render rows as a JSON string."""
    payload: Any = {"results": _to_serializable(rows)}
    if title:
        payload["title"] = title
    return json.dumps(payload, indent=2)


def format_as_csv(rows: List[Dict[str, Any]], title: Optional[str] = None) -> str:
    """Render rows as CSV text (title is ignored for CSV)."""
    if not rows:
        return ""
    buf = io.StringIO()
    headers = list(rows[0].keys())
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({h: row.get(h, "") for h in headers})
    return buf.getvalue()


def render(
    rows: List[Dict[str, Any]],
    mode: OutputMode = "text",
    title: Optional[str] = None,
) -> str:
    """Dispatch to the appropriate formatter based on *mode*."""
    if mode == "json":
        return format_as_json(rows, title)
    if mode == "csv":
        return format_as_csv(rows, title)
    return format_as_text(rows, title)
