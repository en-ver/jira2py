"""Custom exceptions for jira2py.

This module defines a hierarchy of exceptions for jira2py that allow users
to handle specific error conditions while preserving original tracebacks via
exception chaining.
"""

from __future__ import annotations

import httpx


class JiraError(Exception):
    """Base exception for all jira2py errors.

    All jira2py exceptions inherit from this class, allowing users to catch
    any library-specific error with a single except clause.

    Attributes:
        message: Human-readable error message
        response: Optional httpx.Response object for HTTP-related errors

    Example:
        >>> try:
        ...     jira.get_issue("PROJ-123")
        ... except JiraError as e:
        ...     print(f"JIRA error: {e}")
    """

    def __init__(self, message: str, *, response: httpx.Response | None = None):
        self.message = message
        self.response = response
        super().__init__(message)


class JiraAuthenticationError(JiraError):
    """Raised when authentication or authorization fails.

    Typically raised for HTTP 401 (unauthorized) or 403 (forbidden) responses.

    Example:
        >>> try:
        ...     jira.get_issue("PROJ-123")
        ... except JiraAuthenticationError:
        ...     print("Invalid credentials or insufficient permissions")
    """

    pass


class JiraConnectionError(JiraError):
    """Raised when network or connection issues occur.

    Covers timeouts, DNS failures, connection refused, and other network-level
    errors that prevent communication with the JIRA API.

    Example:
        >>> try:
        ...     jira.get_issue("PROJ-123")
        ... except JiraConnectionError:
        ...     print("Network error - check your connection")
    """

    pass


class JiraAPIError(JiraError):
    """Raised for HTTP 4xx/5xx errors from the JIRA API.

    Provides detailed information about the API error including status code,
    response object, and parsed error messages from JIRA.

    Attributes:
        status_code: HTTP status code
        response: Full httpx.Response object
        error_messages: List of error messages extracted from JIRA response

    Example:
        >>> try:
        ...     jira.get_issue("PROJ-123")
        ... except JiraAPIError as e:
        ...     print(f"API error {e.status_code}: {e.error_messages}")
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response: httpx.Response,
        error_messages: list[str] | None = None,
    ):
        self.status_code = status_code
        self.error_messages = error_messages or []
        super().__init__(message, response=response)


class JiraNotFoundError(JiraAPIError):
    """Raised when a requested resource is not found (HTTP 404).

    Example:
        >>> try:
        ...     jira.get_issue("NONEXISTENT-123")
        ... except JiraNotFoundError:
        ...     print("Issue does not exist")
    """

    pass


class JiraRateLimitError(JiraAPIError):
    """Raised when API rate limit is exceeded (HTTP 429).

    Example:
        >>> try:
        ...     # Many rapid requests
        ...     issues = [jira.get_issue(f"PROJ-{i}") for i in range(1000)]
        ... except JiraRateLimitError:
        ...     print("Rate limit exceeded - implement backoff")
    """

    pass


class JiraValidationError(JiraAPIError):
    """Raised when request validation fails (HTTP 400).

    Indicates that the request was malformed or contained invalid data.

    Example:
        >>> try:
        ...     jira.create_issue({"project": None})  # Invalid data
        ... except JiraValidationError as e:
        ...     print(f"Validation failed: {e.error_messages}")
    """

    pass
