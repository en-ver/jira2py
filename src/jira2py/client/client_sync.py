"""Synchronous JIRA client implementation."""

import atexit
import contextlib
import logging
import random
import threading
from collections.abc import Mapping
from typing import Any, NoReturn

import httpx
from tenacity import (
    RetryCallState,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from jira2py.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)

from .credentials import JiraCredentials

logger = logging.getLogger("jira2py")

# Default HTTP client configuration
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_CONNECT_TIMEOUT = 10.0
_DEFAULT_POOL_TIMEOUT = 5.0
_DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
_DEFAULT_MAX_CONNECTIONS = 50
_DEFAULT_KEEPALIVE_EXPIRY = 30.0

# Default retry configuration (per Atlassian official documentation)
_DEFAULT_MAX_RETRIES = 4
_DEFAULT_INITIAL_RETRY_DELAY = 5.0
_DEFAULT_MAX_RETRY_DELAY = 30.0
_DEFAULT_JITTER_RANGE = (0.7, 1.3)

# HTTP header and status code constants
_HEADER_RETRY_AFTER = "Retry-After"
_HEADER_RATELIMIT_REASON = "RateLimit-Reason"
_STATUS_RATE_LIMITED = 429


def _create_httpx_client(credentials: JiraCredentials) -> httpx.Client:
    """Create an httpx.Client configured for the JIRA API.

    Args:
        credentials: JIRA authentication credentials.

    Returns:
        httpx.Client instance with connection pooling, timeouts, and auth.
    """
    return httpx.Client(
        base_url=f"{credentials.url}/rest/api/3",
        headers={"Accept": "application/json"},
        auth=httpx.BasicAuth(credentials.username, credentials.api_token),
        limits=httpx.Limits(
            max_keepalive_connections=_DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
            max_connections=_DEFAULT_MAX_CONNECTIONS,
            keepalive_expiry=_DEFAULT_KEEPALIVE_EXPIRY,
        ),
        timeout=httpx.Timeout(
            _DEFAULT_TIMEOUT,
            connect=_DEFAULT_CONNECT_TIMEOUT,
            pool=_DEFAULT_POOL_TIMEOUT,
        ),
        http2=True,
    )


class JiraClientSync:
    """Synchronous JIRA client.

    Provides synchronous HTTP requests to the JIRA API with connection pooling
    and automatic retry with exponential backoff on rate limit (429) responses.

    Args:
        credentials: JIRA authentication credentials.
        max_retries: Maximum number of retries on 429 responses. Set to 0 to disable.
        max_retry_delay: Maximum delay in seconds between retries.
    """

    # Class-level storage for shared persistent clients
    _class_persistent_clients: dict[str, httpx.Client] = {}
    _clients_lock = threading.Lock()

    def __init__(
        self,
        credentials: JiraCredentials,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        max_retry_delay: float = _DEFAULT_MAX_RETRY_DELAY,
    ) -> None:
        """Initialize the synchronous client.

        Args:
            credentials: JIRA authentication credentials.
            max_retries: Maximum number of retries on 429 responses. Set to 0 to disable.
            max_retry_delay: Maximum delay in seconds between retries.
        """
        self.credentials = credentials
        self._max_retries = max_retries
        self._max_retry_delay = max_retry_delay
        self._client_key = (
            f"{credentials.url}:{credentials.username}:{credentials.api_token}"
        )
        self._backoff = wait_exponential(
            multiplier=_DEFAULT_INITIAL_RETRY_DELAY,
            min=_DEFAULT_INITIAL_RETRY_DELAY,
            max=float("inf"),
        )

    def _get_persistent_client(self) -> httpx.Client:
        """Get or create a persistent HTTP client for connection pooling.

        Uses double-checked locking for thread safety.

        Returns:
            The persistent HTTP client instance.
        """
        if self._client_key not in self._class_persistent_clients:
            with self._clients_lock:
                if self._client_key not in self._class_persistent_clients:
                    self._class_persistent_clients[self._client_key] = (
                        _create_httpx_client(self.credentials)
                    )
        return self._class_persistent_clients[self._client_key]

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Make a synchronous request to the JIRA API.

        Automatically retries on HTTP 429 (rate limit) responses with exponential
        backoff and jitter, respecting the ``Retry-After`` header when present.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash).
            params: Query parameters.
            data: Request body data.
            extra_params: Additional query parameters. Keys in extra_params take priority
                over named parameters and can be used to override or extend them.
            extra_data: Additional body data. Keys in extra_data take priority over named
                data parameters and can be used to override or extend them.

        Returns:
            Response data as dict, list, or None for empty responses.
        """
        # Merge parameters; strip None from query params (httpx sends None as "None")
        # extra_params takes priority over params (later keys win in dict merge)
        merged_params = {
            k: v
            for k, v in {**(params or {}), **(extra_params or {})}.items()
            if v is not None
        }
        # Preserve None in body data (serialized as JSON null, needed to clear fields)
        # extra_data takes priority over data (later keys win in dict merge)
        merged_data = {**(data or {}), **(extra_data or {})}

        request_kwargs: dict[str, Any] = {}
        if merged_params:
            request_kwargs["params"] = merged_params
        if merged_data:
            request_kwargs["json"] = merged_data

        client = self._get_persistent_client()

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self._max_retries + 1),
                wait=self._wait_for_retry,
                retry=retry_if_exception(self._is_retryable),
                before_sleep=self._log_retry,
                reraise=True,
            ):
                with attempt:
                    response = client.request(method, context_path, **request_kwargs)
                    response.raise_for_status()
        except Exception as e:
            self._handle_error(e)

        return self._handle_response(response)

    @staticmethod
    def _is_retryable(error: BaseException) -> bool:
        """Check if an error is retryable (HTTP 429 only)."""
        return (
            isinstance(error, httpx.HTTPStatusError)
            and error.response.status_code == _STATUS_RATE_LIMITED
        )

    def _wait_for_retry(self, retry_state: RetryCallState) -> float:
        """Calculate wait time for retry, respecting Retry-After header.

        Follows Atlassian's official retry strategy:
        - Use Retry-After header value when present
        - Fall back to exponential backoff: initial_delay * 2^(attempt-1)
        - Apply jitter to avoid thundering herd
        - Cap at max_retry_delay

        When the server provides a Retry-After header, jitter is applied only
        *above* the server-specified minimum (additive, 0–30%) to respect the
        minimum wait. For exponential backoff, multiplicative jitter (0.7x–1.3x)
        is used. The exponential base is computed via ``tenacity.wait_exponential``.
        """
        wait = self._backoff(retry_state)
        has_retry_after = False

        exc = retry_state.outcome.exception() if retry_state.outcome else None
        if isinstance(exc, httpx.HTTPStatusError):
            retry_after = exc.response.headers.get(_HEADER_RETRY_AFTER)
            if retry_after:
                with contextlib.suppress(ValueError):
                    wait = float(retry_after)
                    has_retry_after = True

        if has_retry_after:
            # Additive jitter above the server minimum (0–30%)
            wait += random.uniform(0, wait * 0.3)  # noqa: S311
        else:
            # Multiplicative jitter for exponential backoff
            jitter = random.uniform(*_DEFAULT_JITTER_RANGE)  # noqa: S311
            wait *= jitter

        return min(wait, self._max_retry_delay)

    @staticmethod
    def _log_retry(retry_state: RetryCallState) -> None:
        """Log retry attempts at WARNING level."""
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = None
        reason = None
        if isinstance(exc, httpx.HTTPStatusError):
            retry_after = exc.response.headers.get(_HEADER_RETRY_AFTER)
            reason = exc.response.headers.get(_HEADER_RATELIMIT_REASON)

        logger.warning(
            "Rate limited by Jira (attempt %d). reason=%s, retry_after=%s",
            retry_state.attempt_number,
            reason,
            retry_after,
        )

    @staticmethod
    def _handle_response(
        response: httpx.Response,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Handle HTTP response and extract JSON data.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON response as dict or list, or None for
            responses with no content (e.g., 204 No Content).

        Raises:
            ValueError: If response has content that cannot be parsed as JSON.
        """
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {e}") from e

    def _extract_error_messages(self, response: httpx.Response) -> list[str]:
        """Extract error messages from JIRA API response.

        Accumulates messages from all error fields in the Jira Error Collection
        schema (``errorMessages``, ``errors``, ``message``). Jira always includes
        both ``errorMessages`` and ``errors`` in error responses, and either or
        both may contain content. Only JSON/encoding parse errors (ValueError,
        UnicodeDecodeError) are suppressed; programming errors propagate.

        Args:
            response: httpx.Response object.

        Returns:
            List of error message strings.
        """
        try:
            data = response.json()
        except (ValueError, UnicodeDecodeError):
            return []

        if not isinstance(data, dict):
            return []

        messages: list[str] = []

        if isinstance(data.get("errorMessages"), list):
            messages.extend(data["errorMessages"])

        if isinstance(data.get("errors"), dict):
            messages.extend(str(v) for v in data["errors"].values())

        if "message" in data:
            messages.append(data["message"])

        return messages

    def _handle_error(self, error: Exception) -> NoReturn:
        """Handle HTTP errors and convert to appropriate jira2py exceptions.

        Args:
            error: The original exception from httpx.

        Raises:
            JiraAuthenticationError: For 401/403 responses.
            JiraNotFoundError: For 404 responses.
            JiraRateLimitError: For 429 responses.
            JiraValidationError: For 400 responses.
            JiraAPIError: For other 4xx/5xx responses.
            JiraConnectionError: For network/timeout errors.
            JiraError: For any other errors.
        """
        if isinstance(error, httpx.HTTPStatusError):
            response = error.response
            status_code = response.status_code
            error_messages = self._extract_error_messages(response)

            if status_code == 401:
                raise JiraAuthenticationError(
                    "Authentication failed. Check your credentials.",
                    status_code=401,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == 403:
                raise JiraAuthenticationError(
                    "Access forbidden. You don't have permission to access this resource.",
                    status_code=403,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == 404:
                raise JiraNotFoundError(
                    "Resource not found.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == _STATUS_RATE_LIMITED:
                retry_after_header = response.headers.get(_HEADER_RETRY_AFTER)
                retry_after = None
                if retry_after_header:
                    with contextlib.suppress(ValueError):
                        retry_after = float(retry_after_header)

                raise JiraRateLimitError(
                    "API rate limit exceeded.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                    retry_after=retry_after,
                    rate_limit_reason=response.headers.get(_HEADER_RATELIMIT_REASON),
                    reset_at=response.headers.get("X-RateLimit-Reset"),
                ) from error

            if status_code == 400:
                raise JiraValidationError(
                    "Request validation failed. Check your input data.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if 400 <= status_code < 500:
                raise JiraAPIError(
                    f"Client error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code >= 500:
                raise JiraAPIError(
                    f"Server error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

        if isinstance(error, httpx.TimeoutException):
            raise JiraConnectionError(
                f"Request timed out: {error}",
            ) from error

        if isinstance(error, httpx.NetworkError):
            raise JiraConnectionError(
                f"Network error: {error}",
            ) from error

        if isinstance(error, httpx.HTTPError):
            raise JiraError(
                f"HTTP error occurred: {error}",
            ) from error

        raise JiraError(
            f"Unexpected error: {error}",
        ) from error

    @classmethod
    def close_all(cls) -> None:
        """Close all persistent clients and release resources."""
        with cls._clients_lock:
            for client in cls._class_persistent_clients.values():
                try:
                    client.close()
                except Exception:
                    logger.debug(
                        "Failed to close HTTP client during cleanup", exc_info=True
                    )
            cls._class_persistent_clients.clear()


# Register cleanup on interpreter exit
atexit.register(JiraClientSync.close_all)
