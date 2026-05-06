"""Tag-based filtering for crontab entries.

Allows entries to be tagged via inline comments (e.g. # tags: backup,critical)
and then filtered by one or more tag names.
"""

import re
from typing import List, Optional
from crontab_audit.parser import CrontabEntry

TAG_PATTERN = re.compile(r"#\s*tags?:\s*([\w,\s-]+)", re.IGNORECASE)


def extract_tags(entry: CrontabEntry) -> List[str]:
    """Extract tags from an entry's command field (inline comment).

    Looks for patterns like: # tags: backup, critical
    Returns a list of lowercased, stripped tag strings.
    """
    match = TAG_PATTERN.search(entry.command)
    if not match:
        return []
    raw = match.group(1)
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def filter_by_tag(
    entries: List[CrontabEntry],
    tag: str,
    require_all: bool = False,
) -> List[CrontabEntry]:
    """Filter entries that match one or more tags.

    Args:
        entries: List of CrontabEntry objects to filter.
        tag: A comma-separated string of tags to match against.
        require_all: If True, entry must have ALL listed tags; otherwise ANY.

    Returns:
        Filtered list of entries.
    """
    wanted = [t.strip().lower() for t in tag.split(",") if t.strip()]
    if not wanted:
        return list(entries)

    result = []
    for entry in entries:
        entry_tags = extract_tags(entry)
        if require_all:
            if all(w in entry_tags for w in wanted):
                result.append(entry)
        else:
            if any(w in entry_tags for w in wanted):
                result.append(entry)
    return result


def group_by_tag(
    entries: List[CrontabEntry],
) -> dict:
    """Group entries by their tags.

    An entry may appear under multiple tag keys.
    Entries with no tags are grouped under the key '__untagged__'.

    Returns:
        Dict mapping tag -> list of CrontabEntry.
    """
    groups: dict = {}
    for entry in entries:
        tags = extract_tags(entry)
        if not tags:
            groups.setdefault("__untagged__", []).append(entry)
        else:
            for tag in tags:
                groups.setdefault(tag, []).append(entry)
    return groups
