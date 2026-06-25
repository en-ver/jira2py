from __future__ import annotations

from datetime import UTC, datetime

import pytest

from jira2py.helpers._validation import (
    parse_strict_date,
    require_non_empty_string,
    validate_date_range,
    validate_field_conflicts,
)
from jira2py.helpers.errors import JiraHelperValidationError


def test_require_non_empty_string_rejects_blank_values() -> None:
    assert require_non_empty_string("PROJ-123", field_name="issue_key") == "PROJ-123"

    with pytest.raises(JiraHelperValidationError, match="issue_key"):
        require_non_empty_string("   ", field_name="issue_key")


def test_validate_field_conflicts_rejects_reserved_keys() -> None:
    with pytest.raises(
        JiraHelperValidationError,
        match="summary, description",
    ):
        validate_field_conflicts(
            {"summary": "hello", "description": "world", "labels": ["x"]},
            reserved_fields={"summary", "description"},
        )


def test_parse_strict_date_requires_yyyy_mm_dd() -> None:
    assert (
        parse_strict_date("2026-01-02", field_name="start_date").isoformat()
        == "2026-01-02"
    )

    with pytest.raises(JiraHelperValidationError, match="start_date"):
        parse_strict_date("2026/01/02", field_name="start_date")


def test_validate_date_range_returns_utc_boundaries() -> None:
    start_dt, end_dt = validate_date_range(
        start_date="2026-01-02",
        end_date="2026-01-03",
    )

    assert start_dt == datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    assert end_dt == datetime(2026, 1, 4, 0, 0, tzinfo=UTC)


def test_validate_date_range_rejects_descending_ranges() -> None:
    with pytest.raises(
        JiraHelperValidationError,
        match="end_date must be on or after start_date",
    ):
        validate_date_range(start_date="2026-01-03", end_date="2026-01-02")
