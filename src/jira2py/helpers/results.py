"""Foundational result contracts for jira2py helper operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class HelperResult:
    """Human-readable helper output plus optional structured/raw payloads."""

    text: str
    data: Any | None = None
    raw_content: str | None = None

    @property
    def has_raw_output(self) -> bool:
        """Whether the result carries structured or serialized raw output."""
        return self.data is not None or self.raw_content is not None

    @classmethod
    def text_only(cls, text: str) -> HelperResult:
        """Create a text-only result."""
        return cls(text=text)

    @classmethod
    def with_data(
        cls,
        text: str,
        data: Any,
        *,
        raw_content: str | None = None,
    ) -> HelperResult:
        """Create a result with structured data and optional raw content."""
        return cls(text=text, data=data, raw_content=raw_content)


__all__ = ["HelperResult"]
