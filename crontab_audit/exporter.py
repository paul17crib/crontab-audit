"""Export audit results to JSON or CSV formats."""

import csv
import json
import io
from typing import List
from crontab_audit.reporter import AuditReport


def export_json(report: AuditReport, indent: int = 2) -> str:
    """Serialize an AuditReport to a JSON string."""
    data = {
        "summary": {
            "total_entries": report.summary["total_entries"],
            "total_risks": report.summary["total_risks"],
            "total_overlaps": report.summary["total_overlaps"],
            "total_validation_errors": report.summary["total_validation_errors"],
        },
        "risks": [
            {
                "host": flag.entry.host,
                "command": flag.entry.command,
                "schedule": str(flag.entry),
                "reason": flag.reason,
            }
            for flag in report.risks
        ],
        "overlaps": [
            {
                "host": result.entry_a.host,
                "command_a": result.entry_a.command,
                "command_b": result.entry_b.command,
                "overlap_times": result.overlap_times[:10],
            }
            for result in report.overlaps
        ],
        "validation_errors": [
            {
                "host": err.entry.host if err.entry else None,
                "field": err.field,
                "message": str(err),
            }
            for err in report.validation_errors
        ],
    }
    return json.dumps(data, indent=indent)


def export_csv(report: AuditReport) -> str:
    """Serialize risk flags from an AuditReport to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["type", "host", "command", "detail"])

    for flag in report.risks:
        writer.writerow([
            "risk",
            flag.entry.host or "",
            flag.entry.command,
            flag.reason,
        ])

    for result in report.overlaps:
        writer.writerow([
            "overlap",
            result.entry_a.host or "",
            f"{result.entry_a.command} / {result.entry_b.command}",
            f"{len(result.overlap_times)} overlapping time(s)",
        ])

    for err in report.validation_errors:
        writer.writerow([
            "validation_error",
            err.entry.host if err.entry else "",
            "",
            str(err),
        ])

    return output.getvalue()
