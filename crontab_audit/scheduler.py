"""Schedule analysis utilities: next-run time estimation and frequency classification."""

from datetime import datetime, timedelta
from typing import Optional
from crontab_audit.parser import CrontabEntry


FREQUENCY_LABELS = {
    "yearly": 365 * 24 * 60,
    "monthly": 30 * 24 * 60,
    "weekly": 7 * 24 * 60,
    "daily": 24 * 60,
    "hourly": 60,
    "sub-hourly": 0,
}


def _field_min(field: str, min_val: int, max_val: int) -> int:
    """Return the smallest concrete value from a cron field string."""
    if field == "*":
        return min_val
    if "," in field:
        return min(int(v) for v in field.split(","))
    if "-" in field and "/" not in field:
        return int(field.split("-")[0])
    if field.startswith("*/"):
        return min_val
    if "/" in field:
        base, _ = field.split("/")
        return int(base) if base != "*" else min_val
    return int(field)


def estimate_next_run(entry: CrontabEntry, after: Optional[datetime] = None) -> datetime:
    """Estimate the next run time for a crontab entry after a given datetime.

    This is a best-effort approximation using the minimum concrete values from
    each field.  It is not a full cron scheduler.
    """
    if after is None:
        after = datetime.now().replace(second=0, microsecond=0)

    fields = entry.schedule_fields()
    minute = _field_min(fields["minute"], 0, 59)
    hour = _field_min(fields["hour"], 0, 23)
    day = _field_min(fields["day"], 1, 28)
    month = _field_min(fields["month"], 1, 12)

    candidate = after.replace(
        month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate <= after:
        candidate += timedelta(days=1)
    return candidate


def classify_frequency(entry: CrontabEntry) -> str:
    """Return a human-readable frequency label for a crontab entry."""
    fields = entry.schedule_fields()
    minute = fields["minute"]
    hour = fields["hour"]
    day = fields["day"]
    month = fields["month"]

    if month != "*":
        return "yearly"
    if day != "*":
        return "monthly"
    if hour != "*":
        return "daily"
    if minute == "*" or (minute.startswith("*/") and int(minute[2:]) < 60):
        step = int(minute[2:]) if minute.startswith("*/") else 1
        if step < 60:
            return "sub-hourly"
    return "hourly"
