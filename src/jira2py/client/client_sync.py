"""Synchronous JIRA client implementation."""

import atexit
import contextlib
import threading
from collections.abc import Mapping
from typing import Any, NoReturn

import httpx

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

# Default HTTP client configuration
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_CONNECT_TIMEOUT = 10.0
_DEFAULT_POOL_TIMEOUT = 5.0
_DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
_DEFAULT_MAX_CONNECTIONS = 50
_DEFAULT_KEEPALIVE_EXPIRY = 30.0


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

    Provides synchronous HTTP requests to the JIRA API with connection pooling.

    Args:
        credentials: JIRA authentication credentials.
    """

    # Class-level storage for shared persistent clients
    _class_persistent_clients: dict[str, httpx.Client] = {}
    _clients_lock = threading.Lock()

    def __init__(self, credentials: JiraCredentials) -> None:
        """Initialize the synchronous client.

        Args:
            credentials: JIRA authentication credentials.
        """
        self.credentials = credentials
        self._client_key = f"{credentials.url}:{credentials.username or 'anonymous'}"

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

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash).
            params: Query parameters.
            data: Request body data.
            extra_params: Additional query parameters (lower priority than params).
            extra_data: Additional body data (lower priority than data).

        Returns:
            Response data as dict, list, or None for empty responses.
        """
        # Merge parameters; strip None from query params (httpx sends None as "None")
        merged_params = {
            k: v
            for k, v in {**(extra_params or {}), **(params or {})}.items()
            if v is not None
        }
        # Preserve None in body data (serialized as JSON null, needed to clear fields)
        merged_data = {**(extra_data or {}), **(data or {})}

        request_kwargs: dict[str, Any] = {}
        if merged_params:
            request_kwargs["params"] = merged_params
        if merged_data:
            request_kwargs["json"] = merged_data

        client = self._get_persistent_client()

        try:
            response = client.request(method, context_path, **request_kwargs)
            response.raise_for_status()
        except Exception as e:
            self._handle_error(e)

        return self._handle_response(response)

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

        Args:
            response: httpx.Response object.

        Returns:
            List of error message strings.
        """
        try:
            data = response.json()

            if isinstance(data, dict):
                if "errorMessages" in data:
                    error_msgs = data["errorMessages"]
                    return error_msgs if isinstance(error_msgs, list) else [error_msgs]
                if "errors" in data:
                    errors = data["errors"]
                    return (
                        list(errors.values())
                        if isinstance(errors, dict)
                        else [str(errors)]
                    )
                if "message" in data:
                    return [data["message"]]

            return []
        except Exception:
            return []

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
                    response=response,
                ) from error

            if status_code == 403:
                raise JiraAuthenticationError(
                    "Access forbidden. You don't have permission to access this resource.",
                    response=response,
                ) from error

            if status_code == 404:
                raise JiraNotFoundError(
                    "Resource not found.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            if status_code == 429:
                raise JiraRateLimitError(
                    "API rate limit exceeded. Implement backoff and retry.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
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
                with contextlib.suppress(Exception):
                    client.close()
            cls._class_persistent_clients.clear()


# Register cleanup on interpreter exit
atexit.register(JiraClientSync.close_all)
