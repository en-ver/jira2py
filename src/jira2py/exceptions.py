"""Custom low-level exceptions for jira2py.

This hierarchy covers HTTP, transport, and attachment-protocol failures; it is
not a catch-all for every exception a jira2py call can raise. Many wrappers use
exception chaining, but security-sensitive paths and directly raised errors may
not retain a cause.
"""

from __future__ import annotations

import httpx


class JiraError(Exception):
    """Base exception for jira2py's custom low-level errors.

    Covers HTTP, transport, and attachment-protocol failures. It is not a
    catch-all: helper errors use an independent hierarchy, and built-in or
    model-validation errors may also occur.

    Attributes:
        message: Human-readable error message
        response: Optional httpx.Response object for HTTP-related errors

    Example:
        >>> try:
        ...     jira.issues.get_issue("PROJ-123")
        ... except JiraError as e:
        ...     print(f"JIRA error: {e}")
    """

    def __init__(self, message: str, *, response: httpx.Response | None = None):
        self.message = message
        self.response = response
        super().__init__(message)


class JiraConnectionError(JiraError):
    """Raised when network or connection issues occur.

    Covers timeouts, DNS failures, connection refused, and other network-level
    errors that prevent communication with the JIRA API.

    Example:
        >>> try:
        ...     jira.issues.get_issue("PROJ-123")
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
        response: Full httpx.Response object when available, otherwise ``None``
        error_messages: List of error messages extracted from JIRA response

    Example:
        >>> try:
        ...     jira.issues.get_issue("PROJ-123")
        ... except JiraAPIError as e:
        ...     print(f"API error {e.status_code}: {e.error_messages}")
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response: httpx.Response | None,
        error_messages: list[str] | None = None,
    ):
        self.status_code = status_code
        self.error_messages = error_messages or []
        super().__init__(message, response=response)


class JiraAuthenticationError(JiraAPIError):
    """Raised when authentication or authorization fails.

    Inherits from ``JiraAPIError``, so callers using ``except JiraAPIError`` will
    also catch this exception (unlike before this change).

    Typically raised for HTTP 401 (unauthorized) or 403 (forbidden) responses.
    The ``status_code`` attribute (401 or 403) can be used to distinguish the
    two cases. The ``error_messages`` attribute contains any additional error
    details from the Jira response.

    Attributes:
        status_code: HTTP status code (401 or 403).
        response: Full httpx.Response object when available, otherwise ``None``.
        error_messages: List of error messages extracted from JIRA response.

    Example:
        >>> try:
        ...     jira.issues.get_issue("PROJ-123")
        ... except JiraAuthenticationError as e:
        ...     print(f"Auth failed ({e.status_code}): invalid credentials or insufficient permissions")
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 401,
        response: httpx.Response | None = None,
        error_messages: list[str] | None = None,
    ):
        super().__init__(
            message,
            status_code=status_code,
            response=response,
            error_messages=error_messages,
        )


class JiraNotFoundError(JiraAPIError):
    """Raised when a requested resource is not found (HTTP 404).

    Example:
        >>> try:
        ...     jira.issues.get_issue("NONEXISTENT-123")
        ... except JiraNotFoundError:
        ...     print("Issue does not exist")
    """

    pass


class JiraRateLimitError(JiraAPIError):
    """Raised when API rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header).
        rate_limit_reason: Which limit was hit (from RateLimit-Reason header).
            Values: ``jira-burst-based``, ``jira-quota-global-based``,
            ``jira-quota-tenant-based``, ``jira-per-issue-on-write``.
        reset_at: ISO 8601 timestamp when the rate limit window resets
            (from X-RateLimit-Reset header).

    Example:
        >>> try:
        ...     issues = [jira.issues.get_issue(f"PROJ-{i}") for i in range(1000)]
        ... except JiraRateLimitError as e:
        ...     print(f"Rate limited: retry after {e.retry_after}s, reason: {e.rate_limit_reason}")
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response: httpx.Response | None,
        error_messages: list[str] | None = None,
        retry_after: float | None = None,
        rate_limit_reason: str | None = None,
        reset_at: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            response=response,
            error_messages=error_messages,
        )
        self.retry_after = retry_after
        self.rate_limit_reason = rate_limit_reason
        self.reset_at = reset_at


class JiraValidationError(JiraAPIError):
    """Raised when request validation fails (HTTP 400).

    Indicates that the request was malformed or contained invalid data.

    Example:
        >>> try:
        ...     jira.issues.create_issue(fields={"project": None})  # Invalid data
        ... except JiraValidationError as e:
        ...     print(f"Validation failed: {e.error_messages}")
    """

    pass
