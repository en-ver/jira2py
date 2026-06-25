"""Internal helper utilities for formatting jira2py helper output."""

from __future__ import annotations

import math


def format_size(size: int | float) -> str:
    """Format a byte count into a human-readable size string."""
    if (
        not isinstance(size, (int, float))
        or math.isnan(size)
        or not math.isfinite(size)
        or size < 0
    ):
        return "unknown size"
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{int(size)} bytes"


def format_date(date_str: str | None) -> str:
    """Format an ISO-like Jira date string as YYYY-MM-DD."""
    if not date_str:
        return "—"
    return date_str[:10]
