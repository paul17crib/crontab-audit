"""Detects crontab entries that appear to be part of a command chain
or pipeline, flagging potential issues with chained execution."""

from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.parser import CrontabEntry


@dataclass
class ChainIssue:
    entry: CrontabEntry
    reason: str
    severity: str  # "warning" or "info"
    chain_tokens: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        cmd = self.entry.command
        tokens = ", ".join(self.chain_tokens) if self.chain_tokens else ""
        parts = [f"[{self.severity.upper()}] {host}: {cmd}"]
        parts.append(f"  Reason: {self.reason}")
        if tokens:
            parts.append(f"  Chain tokens: {tokens}")
        return "\n".join(parts)


def _extract_chain_tokens(command: str) -> List[str]:
    """Return shell chaining operators found in the command."""
    tokens = []
    for op in ["||", "&&", ";", "|"]:
        if op in command:
            tokens.append(op)
    return list(dict.fromkeys(tokens))  # preserve order, deduplicate


def _is_pipe_to_shell(command: str) -> bool:
    """Detect dangerous pipe-to-shell patterns."""
    dangerous = ["| bash", "|bash", "| sh", "|sh", "| python", "|python"]
    return any(pat in command for pat in dangerous)


def _is_silent_failure(command: str) -> bool:
    """Detect chains that suppress errors (e.g. cmd || true)."""
    return "|| true" in command or "|| exit 0" in command


def check_chains(entries: List[CrontabEntry]) -> List[ChainIssue]:
    """Analyse entries for chained command issues."""
    issues: List[ChainIssue] = []
    for entry in entries:
        cmd = entry.command
        tokens = _extract_chain_tokens(cmd)
        if not tokens:
            continue
        if _is_pipe_to_shell(cmd):
            issues.append(ChainIssue(
                entry=entry,
                reason="Command pipes output directly into a shell interpreter",
                severity="warning",
                chain_tokens=tokens,
            ))
        elif _is_silent_failure(cmd):
            issues.append(ChainIssue(
                entry=entry,
                reason="Chain suppresses failure with '|| true' or '|| exit 0'",
                severity="warning",
                chain_tokens=tokens,
            ))
        elif "|" in tokens or "&&" in tokens or ";" in tokens:
            issues.append(ChainIssue(
                entry=entry,
                reason="Command uses shell chaining operators",
                severity="info",
                chain_tokens=tokens,
            ))
    return issues
