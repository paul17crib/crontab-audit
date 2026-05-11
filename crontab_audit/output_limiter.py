"""Limits and paginates audit output for large multi-host reports."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PagedOutput:
    """Holds a single page of lines and pagination metadata."""
    lines: List[str]
    page: int
    total_pages: int
    total_lines: int
    page_size: int

    def has_next(self) -> bool:
        return self.page < self.total_pages

    def has_prev(self) -> bool:
        return self.page > 1

    def __str__(self) -> str:
        header = f"--- Page {self.page}/{self.total_pages} ({self.total_lines} total lines) ---"
        footer = f"--- End of page {self.page} ---"
        return "\n".join([header] + self.lines + [footer])


def paginate(lines: List[str], page: int = 1, page_size: int = 50) -> PagedOutput:
    """Return a PagedOutput for the requested page of lines."""
    if page_size < 1:
        raise ValueError("page_size must be at least 1")
    total_lines = len(lines)
    total_pages = max(1, (total_lines + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return PagedOutput(
        lines=lines[start:end],
        page=page,
        total_pages=total_pages,
        total_lines=total_lines,
        page_size=page_size,
    )


def truncate(lines: List[str], max_lines: int, ellipsis_msg: Optional[str] = None) -> List[str]:
    """Truncate lines to max_lines, appending an ellipsis message if truncated."""
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")
    if len(lines) <= max_lines:
        return list(lines)
    truncated = lines[:max_lines]
    msg = ellipsis_msg or f"... ({len(lines) - max_lines} more lines not shown)"
    truncated.append(msg)
    return truncated


def filter_lines(lines: List[str], keyword: str, case_sensitive: bool = False) -> List[str]:
    """Return only lines containing keyword."""
    if not case_sensitive:
        keyword = keyword.lower()
        return [l for l in lines if keyword in l.lower()]
    return [l for l in lines if keyword in l]


def summarize(lines: List[str], max_lines: int = 10) -> str:
    """Return a brief summary of lines, showing the first few and a count of the rest.

    Useful for embedding a compact overview of a large report section in emails
    or log output without overwhelming the reader.

    Args:
        lines: The full list of output lines to summarize.
        max_lines: Maximum number of lines to include before summarizing the rest.

    Returns:
        A single string with up to max_lines lines followed by a remainder note.
    """
    if max_lines < 1:
        raise ValueError("max_lines must be at least 1")
    if len(lines) <= max_lines:
        return "\n".join(lines)
    shown = lines[:max_lines]
    remaining = len(lines) - max_lines
    shown.append(f"... and {remaining} more line{'s' if remaining != 1 else ''}.")
    return "\n".join(shown)
