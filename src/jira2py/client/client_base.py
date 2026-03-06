"""Base JIRA client implementation."""

import atexit
import contextlib
import threading
from abc import ABC, abstractmethod
from typing import Any

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
from .factory import JiraClientFactory


class JiraClientBase(ABC):
    """Abstract base class for JIRA clients.

    This class provides common functionality for both sync and async JIRA clients.
    It handles credentials management, request preparation, and response handling.

    Args:
        credentials: JIRA authentication credentials.
    """

    # Class-level storage for shared persistent clients
    _class_persistent_clients: dict[str, httpx.Client | httpx.AsyncClient] = {}
    _clients_lock = threading.Lock()
    _atexit_registered: bool = False

    def __init__(self, credentials: JiraCredentials):
        """Initialize the client with credentials.

        Args:
            credentials: JIRA authentication credentials.
        """
        self.credentials = credentials
        self._client: Any = None
        self._persistent_client: httpx.Client | httpx.AsyncClient | None = None
        self._async_mode = self._get_async_mode()  # Cache for performance
        self._client_key = self._get_client_key()

        # Register atexit cleanup exactly once on the base class
        if not JiraClientBase._atexit_registered:
            atexit.register(JiraClientBase.close_all)
            JiraClientBase._atexit_registered = True

    def _validate_client_type(self, client: httpx.Client | httpx.AsyncClient) -> None:
        """Validate client type matches expected type.

        Args:
            client: The HTTP client instance to validate.

        Raises:
            AssertionError: If client type doesn't match expected type.
        """
        expected_type = self._get_client_type()
        if not isinstance(client, expected_type):
            raise TypeError(f"Expected {expected_type.__name__}")

    def _get_persistent_client(self) -> httpx.Client | httpx.AsyncClient:
        """Get or create a persistent HTTP client for connection pooling.

        Uses double-checked locking for thread safety.

        Returns:
            The persistent HTTP client instance.
        """
        if self._client_key not in self._class_persistent_clients:
            with self._clients_lock:
                if self._client_key not in self._class_persistent_clients:
                    client = JiraClientFactory.create_client(
                        self.credentials, async_mode=self._async_mode
                    )
                    self._validate_client_type(client)
                    self._class_persistent_clients[self._client_key] = client

        client = self._class_persistent_clients[self._client_key]
        self._persistent_client = client
        return client

    @abstractmethod
    def _get_client_type(self) -> type[httpx.Client | httpx.AsyncClient]:
        """Return the expected client type for this implementation.

        Returns:
            Type[Union[httpx.Client, httpx.AsyncClient]]: The client type.
        """
        pass

    @abstractmethod
    def _get_async_mode(self) -> bool:
        """Return whether this client implementation is asynchronous.

        Returns:
            bool: True for async clients, False for sync clients.
        """
        pass

    def _request_jira_base(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        extra_params: dict[str, Any] | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the JIRA API using the provided HTTP call function.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash)
            params: Query parameters
            data: Request body data

        Returns:
            Tuple of (client, method, full_url, request_kwargs).
        """
        # Prepare request parameters
        method, full_url, request_kwargs = self._prepare_request(
            method, context_path, params, data, extra_params, extra_data
        )

        # Use context client if available, otherwise get persistent client
        client = (
            self._client if self._client is not None else self._get_persistent_client()
        )

        # Return client and request kwargs for the specific HTTP call
        return client, method, full_url, request_kwargs

    def _prepare_request(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        extra_params: dict[str, Any] | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> tuple[str, str, dict[str, Any]]:
        """Prepare request parameters.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash)
            params: Query parameters
            data: Request body data

        Returns:
            Tuple of (method, full_url, request_kwargs)
        """
        # Merge dictionaries just before cleaning
        merged_params = self._merge_dict(extra_params, params or {})
        merged_data = self._merge_dict(extra_data, data or {})

        # Clean up merged params and data
        clean_params = self._clean_none_values(merged_params)
        clean_data = self._clean_none_values(merged_data)

        # Construct full URL (httpx will prepend base_url automatically)
        full_url = context_path.lstrip("/")

        # Prepare request kwargs
        request_kwargs: dict[str, Any] = {
            "headers": {"Accept": "application/json"},
        }

        if clean_params:
            request_kwargs["params"] = clean_params

        if clean_data:
            request_kwargs["json"] = clean_data

        return method, full_url, request_kwargs

    def _merge_dict(
        self, extra_dict: dict[str, Any] | None, public_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge two dictionaries with public parameters having higher priority.

        When both dictionaries contain the same key, the value from public_dict
        takes precedence over the value from extra_dict. This allows users to
        provide additional parameters while ensuring explicitly defined public
        API parameters are never overridden.

        Args:
            extra_dict: Additional parameters provided by user (lower priority)
            public_dict: Public API parameters (higher priority)

        Returns:
            Merged dictionary where public parameters override extra parameters

        Example:
            >>> extra = {"param1": "value1", "param2": "value2"}
            >>> public = {"param2": "override", "param3": "value3"}
            >>> result = self._merge_dict(extra, public)
            >>> # Result: {"param1": "value1", "param2": "override", "param3": "value3"}
        """
        if extra_dict is None:
            return public_dict
        return {**extra_dict, **public_dict}

    def _clean_none_values(self, data: Any) -> Any:
        """Recursively remove keys with None values from nested dictionaries and lists.

        Args:
            data: Data to clean

        Returns:
            Cleaned data with None values removed.
        """
        if data is None:
            return None
        elif isinstance(data, dict):
            return {
                k: self._clean_none_values(v) for k, v in data.items() if v is not None
            }
        elif isinstance(data, list):
            return [self._clean_none_values(item) for item in data if item is not None]
        else:
            return data

    def _handle_response(
        self, response: httpx.Response
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Handle HTTP response and extract JSON data.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response as dict or list, or None for
            responses with no content (e.g., 204 No Content).

        Raises:
            ValueError: If response has content that cannot be parsed as JSON.
        """
        # 204 No Content and other empty-body responses are valid successes
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {e}") from e

    def _extract_error_messages(self, response: httpx.Response) -> list[str]:
        """Extract error messages from JIRA API response.

        JIRA error responses can have different structures. This method
        extracts error messages from common locations in the response body.

        Args:
            response: httpx.Response object

        Returns:
            List of error message strings
        """
        try:
            data = response.json()

            # JIRA error responses can have different structures
            if isinstance(data, dict):
                # Check for error messages in common locations
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

    def _handle_error(self, error: Exception) -> None:
        """Handle HTTP errors and convert to appropriate jira2py exceptions.

        This method transforms httpx exceptions into domain-specific jira2py
        exceptions while preserving the original traceback via exception chaining.

        Uses the `raise ... from ...` pattern as recommended by PEP 8 and the
        official Python documentation to preserve the full stack trace.

        Args:
            error: The original exception from httpx

        Raises:
            JiraAuthenticationError: For 401/403 responses
            JiraNotFoundError: For 404 responses
            JiraRateLimitError: For 429 responses
            JiraValidationError: For 400 responses
            JiraAPIError: For other 4xx/5xx responses
            JiraConnectionError: For network/timeout errors
            JiraError: For any other errors
        """
        # Handle HTTP status errors (4xx, 5xx)
        if isinstance(error, httpx.HTTPStatusError):
            response = error.response
            status_code = response.status_code
            error_messages = self._extract_error_messages(response)

            # Map specific status codes to appropriate exceptions
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

            # Handle 400 validation errors
            if status_code == 400:
                raise JiraValidationError(
                    "Request validation failed. Check your input data.",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            # Handle other 4xx client errors
            if 400 <= status_code < 500:
                raise JiraAPIError(
                    f"Client error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

            # Handle 5xx server errors
            if status_code >= 500:
                raise JiraAPIError(
                    f"Server error: {status_code}",
                    status_code=status_code,
                    response=response,
                    error_messages=error_messages,
                ) from error

        # Handle timeout errors
        if isinstance(error, httpx.TimeoutException):
            raise JiraConnectionError(
                f"Request timed out: {error}",
            ) from error

        # Handle network errors (connect, read, write errors)
        if isinstance(error, httpx.NetworkError):
            raise JiraConnectionError(
                f"Network error: {error}",
            ) from error

        # Handle any other httpx errors
        if isinstance(error, httpx.HTTPError):
            raise JiraError(
                f"HTTP error occurred: {error}",
            ) from error

        # Wrap unknown errors in JiraError
        raise JiraError(
            f"Unexpected error: {error}",
        ) from error

    def _get_client_key(self) -> str:
        """Generate unique key for this credentials configuration.

        Returns:
            Unique string key for this client configuration.
        """
        return f"{self.credentials.url}:{self.credentials.username or 'anonymous'}:{self._async_mode}"

    @classmethod
    def close_all(cls) -> None:
        """Close all persistent clients and release resources.

        Call this in test fixtures or application shutdown to ensure
        clean state. Also registered as an atexit handler automatically.
        """
        with cls._clients_lock:
            for client in cls._class_persistent_clients.values():
                with contextlib.suppress(Exception):
                    if isinstance(client, httpx.AsyncClient):
                        import asyncio

                        asyncio.run(client.aclose())
                    elif isinstance(client, httpx.Client):
                        client.close()
            cls._class_persistent_clients.clear()
