"""Foundational error contracts for jira2py helper operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from jira2py.exceptions import JiraAPIError, JiraConnectionError


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


def _mutation_request_error(
    exc: Exception,
    *,
    ordinary_message: str,
    issue_key: str | None = None,
    target: str | None = None,
) -> JiraHelperOperationError:
    """Describe delivery uncertainty only after a direct mutation request failed."""
    if isinstance(exc, JiraConnectionError) or (
        isinstance(exc, JiraAPIError) and 500 <= exc.status_code < 600
    ):
        details: dict[str, Any] = {
            "stage": "mutation_request",
            "mutation_may_have_succeeded": True,
        }
        if issue_key is not None:
            details["issue_key"] = issue_key
        if target is not None:
            details["target"] = target
        return JiraHelperOperationError(
            "Jira may have applied the mutation, but the mutation request failed "
            "before confirmation. Callers must reread the affected resource before "
            "retrying.",
            details=details,
        )
    return JiraHelperOperationError(ordinary_message)


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
