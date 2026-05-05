"""Loads crontab entries from files or raw text for multiple hosts."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crontab_audit.parser import CrontabEntry, CrontabParseError, parse_line


@dataclass
class HostCrontab:
    """Holds parsed crontab entries for a single host."""

    hostname: str
    entries: List[CrontabEntry] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"HostCrontab(hostname={self.hostname!r}, "
            f"entries={len(self.entries)}, errors={len(self.parse_errors)})"
        )


def load_from_text(hostname: str, text: str) -> HostCrontab:
    """Parse raw crontab text for *hostname* and return a HostCrontab."""
    host_crontab = HostCrontab(hostname=hostname)
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        try:
            entry = parse_line(raw_line, hostname=hostname)
            if entry is not None:
                host_crontab.entries.append(entry)
        except CrontabParseError as exc:
            host_crontab.parse_errors.append(f"line {lineno}: {exc}")
    return host_crontab


def load_from_file(filepath: str, hostname: Optional[str] = None) -> HostCrontab:
    """Read a crontab file and return a HostCrontab.

    If *hostname* is not provided the base filename (without extension) is used.
    """
    if hostname is None:
        hostname = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, "r", encoding="utf-8") as fh:
        text = fh.read()
    return load_from_text(hostname, text)


def load_from_directory(directory: str) -> Dict[str, HostCrontab]:
    """Load all *.crontab or *.txt files in *directory*.

    Returns a mapping of hostname -> HostCrontab.
    """
    results: Dict[str, HostCrontab] = {}
    for filename in sorted(os.listdir(directory)):
        if filename.endswith((".crontab", ".txt")):
            filepath = os.path.join(directory, filename)
            host_crontab = load_from_file(filepath)
            results[host_crontab.hostname] = host_crontab
    return results
