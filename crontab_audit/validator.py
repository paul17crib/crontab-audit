"""Validates individual crontab schedule fields."""

from crontab_audit.parser import CrontabEntry

FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),
}


class ValidationError:
    def __init__(self, entry: CrontabEntry, field: str, message: str):
        self.entry = entry
        self.field = field
        self.message = message

    def __str__(self) -> str:
        return f"{self.entry} | field='{self.field}' | {self.message}"


def _validate_field(value: str, field: str, min_val: int, max_val: int) -> list[str]:
    errors = []
    if value == "*":
        return errors

    parts = value.split(",")
    for part in parts:
        if "/" in part:
            base, step = part.split("/", 1)
            if not step.isdigit() or int(step) == 0:
                errors.append(f"Invalid step '{step}' in '{value}'")
            if base != "*":
                parts_to_check = [base]
            else:
                parts_to_check = []
        elif "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2 or not all(b.isdigit() for b in bounds):
                errors.append(f"Invalid range '{part}' in '{value}'")
                continue
            lo, hi = int(bounds[0]), int(bounds[1])
            if lo > hi:
                errors.append(f"Range start > end in '{part}'")
            if lo < min_val or hi > max_val:
                errors.append(f"Range '{part}' out of bounds [{min_val}-{max_val}]")
            parts_to_check = []
        else:
            parts_to_check = [part]

        for p in parts_to_check:
            if not p.isdigit():
                errors.append(f"Non-numeric value '{p}' in '{value}'")
            elif not (min_val <= int(p) <= max_val):
                errors.append(f"Value {p} out of bounds [{min_val}-{max_val}]")

    return errors


def validate_entry(entry: CrontabEntry) -> list[ValidationError]:
    """Validate all schedule fields of a CrontabEntry."""
    errors = []
    field_map = {
        "minute": entry.minute,
        "hour": entry.hour,
        "day_of_month": entry.day_of_month,
        "month": entry.month,
        "day_of_week": entry.day_of_week,
    }
    for field, value in field_map.items():
        min_v, max_v = FIELD_RANGES[field]
        for msg in _validate_field(value, field, min_v, max_v):
            errors.append(ValidationError(entry, field, msg))
    return errors
