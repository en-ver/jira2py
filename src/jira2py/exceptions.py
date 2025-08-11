class JiraBaseError(Exception):
    """Base exception for JiraBase operations."""

    pass


class JiraAuthenticationError(JiraBaseError):
    """Raised when authentication credentials are missing or invalid."""

    pass


class JiraRateLimitError(JiraBaseError):
    """Raised when rate limit is exceeded and max retries reached."""

    pass


class JiraRequestError(JiraBaseError):
    """Raised when a request fails."""

    pass
