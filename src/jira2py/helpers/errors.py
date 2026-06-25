"""Foundational error contracts for jira2py helper operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class JiraHelperError(Exception):
    """Base error for jira2py helper-layer failures."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})


class JiraHelperValidationError(JiraHelperError):
    """Raised when helper input is invalid before a Jira API call."""


class JiraHelperConfigError(JiraHelperError):
    """Raised when helper configuration is missing or invalid."""


class JiraHelperOperationError(JiraHelperError):
    """Raised when a helper-backed Jira API operation fails."""


class AttachmentError(JiraHelperError):
    """Base error for generic attachment-helper failures."""


class AttachmentDownloadError(AttachmentError):
    """Raised when attachment content download fails."""


__all__ = [
    "AttachmentDownloadError",
    "AttachmentError",
    "JiraHelperConfigError",
    "JiraHelperError",
    "JiraHelperOperationError",
    "JiraHelperValidationError",
]
