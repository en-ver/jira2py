"""Internal validation helpers for jira2py high-level helpers."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from .errors import JiraHelperValidationError

_STRICT_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def require_non_empty_string(value: str, *, field_name: str) -> str:
    """Require a non-blank string value."""
    if not isinstance(value, str) or not value.strip():
        raise JiraHelperValidationError(f"{field_name} is required and cannot be empty")
    return value


def validate_field_conflicts(
    fields: Mapping[str, Any] | None,
    *,
    reserved_fields: Collection[str],
) -> None:
    """Reject overlapping explicit parameters and field payload keys."""
    reserved = set(reserved_fields)
    conflicts = [key for key in (fields or {}) if key in reserved]
    if conflicts:
        conflict_list = ", ".join(conflicts)
        raise JiraHelperValidationError(
            f"Use explicit parameters instead of fields for: {conflict_list}"
        )


def parse_strict_date(value: str, *, field_name: str) -> date:
    """Parse a YYYY-MM-DD date string."""
    if _STRICT_DATE_RE.fullmatch(value) is None:
        raise JiraHelperValidationError(f"{field_name} must be in YYYY-MM-DD format.")

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise JiraHelperValidationError(
            f"{field_name} must be in YYYY-MM-DD format."
        ) from exc


def validate_date_range(
    *,
    start_date: str,
    end_date: str,
) -> tuple[datetime, datetime]:
    """Validate an inclusive date range and return UTC boundaries."""
    start_day = parse_strict_date(start_date, field_name="start_date")
    end_day = parse_strict_date(end_date, field_name="end_date")
    if end_day < start_day:
        raise JiraHelperValidationError("end_date must be on or after start_date.")

    start_dt = datetime.combine(start_day, time.min, tzinfo=UTC)
    exclusive_end_dt = datetime.combine(
        end_day + timedelta(days=1),
        time.min,
        tzinfo=UTC,
    )
    return start_dt, exclusive_end_dt
