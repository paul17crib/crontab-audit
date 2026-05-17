"""Lint crontab entries for style and correctness issues."""
from dataclasses import dataclass, field
from typing import List, Optional
from crontab_audit.parser import CrontabEntry


@dataclass
class LintIssue:
    entry: CrontabEntry
    severity: str  # 'warning' | 'error' | 'info'
    code: str
    message: str

    def __str__(self) -> str:
        host = self.entry.host or "unknown"
        return f"[{self.severity.upper()}] {self.code} on {host}: {self.message} (cmd: {self.entry.command})"


# Lint rule codes
_NO_REDIRECT = "L001"
_MISSING_USER = "L002"
_ABSOLUTE_PATH = "L003"
_TRAILING_WHITESPACE = "L004"
_EMPTY_COMMAND = "L005"
_DUPLICATE_SPACES = "L006"


def _check_no_output_redirect(entry: CrontabEntry) -> Optional[LintIssue]:
    """Warn when a command produces output but doesn't redirect it."""
    cmd = entry.command
    has_redirect = any(op in cmd for op in [">>", ">", "2>&1", "/dev/null"])
    looks_noisy = any(t in cmd for t in ["echo", "print", "cat", "ls", "curl", "wget"])
    if looks_noisy and not has_redirect:
        return LintIssue(entry, "warning", _NO_REDIRECT,
                         "Command may produce output without redirect; cron will email output")
    return None


def _check_missing_user(entry: CrontabEntry) -> Optional[LintIssue]:
    """Info when user field is absent."""
    if not entry.user:
        return LintIssue(entry, "info", _MISSING_USER,
                         "No user field set; entry will run as cron owner")
    return None


def _check_absolute_path(entry: CrontabEntry) -> Optional[LintIssue]:
    """Warn when command does not use an absolute path."""
    cmd = entry.command.strip()
    first_token = cmd.split()[0] if cmd.split() else ""
    if first_token and not first_token.startswith("/") and not first_token.startswith("$"):
        return LintIssue(entry, "warning", _ABSOLUTE_PATH,
                         f"Command '{first_token}' is not an absolute path; PATH may differ in cron")
    return None


def _check_trailing_whitespace(entry: CrontabEntry) -> Optional[LintIssue]:
    if entry.command != entry.command.strip():
        return LintIssue(entry, "info", _TRAILING_WHITESPACE,
                         "Command has leading or trailing whitespace")
    return None


def _check_empty_command(entry: CrontabEntry) -> Optional[LintIssue]:
    if not entry.command.strip():
        return LintIssue(entry, "error", _EMPTY_COMMAND, "Command is empty")
    return None


def _check_duplicate_spaces(entry: CrontabEntry) -> Optional[LintIssue]:
    if "  " in entry.command:
        return LintIssue(entry, "info", _DUPLICATE_SPACES,
                         "Command contains consecutive spaces")
    return None


_RULES = [
    _check_empty_command,
    _check_trailing_whitespace,
    _check_duplicate_spaces,
    _check_missing_user,
    _check_absolute_path,
    _check_no_output_redirect,
]


def lint_entry(entry: CrontabEntry) -> List[LintIssue]:
    """Run all lint rules against a single entry."""
    issues: List[LintIssue] = []
    for rule in _RULES:
        result = rule(entry)
        if result is not None:
            issues.append(result)
    return issues


def lint_entries(entries: List[CrontabEntry]) -> List[LintIssue]:
    """Run all lint rules against a list of entries."""
    issues: List[LintIssue] = []
    for entry in entries:
        issues.extend(lint_entry(entry))
    return issues
