"""Classifies crontab entries with human-readable purpose labels based on command patterns."""

from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.parser import CrontabEntry

_LABEL_PATTERNS = [
    ("backup", ["backup", "rsync", "tar ", "dump", "pg_dump", "mysqldump"]),
    ("cleanup", ["rm ", "find ", "clean", "prune", "purge", "rotate"]),
    ("deploy", ["deploy", "ansible", "kubectl", "helm", "docker pull", "git pull"]),
    ("monitoring", ["check", "monitor", "alert", "ping", "healthcheck", "nagios"]),
    ("report", ["report", "digest", "summary", "export", "csv", "pdf"]),
    ("sync", ["sync", "rsync", "sftp", "scp", "fetch", "pull"]),
    ("maintenance", ["vacuum", "optimize", "reindex", "analyze", "defrag"]),
    ("notification", ["mail", "sendmail", "notify", "slack", "webhook", "curl"]),
    ("log", ["logrotate", "log", "audit", "syslog"]),
    ("update", ["apt", "yum", "dnf", "update", "upgrade", "patch"]),
]


@dataclass
class LabeledEntry:
    entry: CrontabEntry
    labels: List[str] = field(default_factory=list)

    def primary_label(self) -> Optional[str]:
        return self.labels[0] if self.labels else None

    def __str__(self) -> str:
        label_str = ", ".join(self.labels) if self.labels else "unknown"
        return f"{self.entry.command} [{label_str}]"


def classify_entry(entry: CrontabEntry) -> LabeledEntry:
    """Assign labels to a single crontab entry based on its command."""
    command_lower = entry.command.lower()
    matched = [
        label
        for label, patterns in _LABEL_PATTERNS
        if any(pat in command_lower for pat in patterns)
    ]
    return LabeledEntry(entry=entry, labels=matched)


def classify_entries(entries: List[CrontabEntry]) -> List[LabeledEntry]:
    """Classify a list of crontab entries."""
    return [classify_entry(e) for e in entries]


def group_by_label(labeled: List[LabeledEntry]) -> dict:
    """Group LabeledEntry objects by their primary label."""
    groups: dict = {}
    for item in labeled:
        key = item.primary_label() or "unknown"
        groups.setdefault(key, []).append(item)
    return groups
