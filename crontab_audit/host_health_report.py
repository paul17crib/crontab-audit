"""Formatting helpers for host health scores."""

from typing import List

from crontab_audit.host_health import HostHealthScore, _grade


def format_score_row(hs: HostHealthScore) -> str:
    grade = _grade(hs.score)
    bar_filled = hs.score // 5
    bar = "#" * bar_filled + "-" * (20 - bar_filled)
    return f"  [{bar}] {hs.score:3d}/100 [{grade}]  {hs.hostname}"


def format_health_report(scores: List[HostHealthScore], verbose: bool = False) -> str:
    if not scores:
        return "No hosts to report."

    lines = ["=== Host Health Report ===", ""]
    for hs in scores:
        lines.append(format_score_row(hs))
        if verbose and hs.penalties:
            for p in hs.penalties:
                lines.append(f"       - {p}")
    lines.append("")

    avg = sum(s.score for s in scores) // len(scores)
    lines.append(f"Hosts evaluated : {len(scores)}")
    lines.append(f"Average score   : {avg}/100  [{_grade(avg)}]")

    healthy = sum(1 for s in scores if s.score >= 75)
    at_risk = len(scores) - healthy
    lines.append(f"Healthy (≥75)   : {healthy}")
    lines.append(f"At risk (<75)   : {at_risk}")
    return "\n".join(lines)


def format_worst_hosts(scores: List[HostHealthScore], n: int = 5) -> str:
    worst = sorted(scores, key=lambda s: s.score)[:n]
    if not worst:
        return "No hosts available."
    lines = [f"=== Bottom {n} Hosts by Health Score ===", ""]
    for hs in worst:
        lines.append(str(hs))
    return "\n".join(lines)
