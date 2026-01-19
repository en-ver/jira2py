"""Base JIRA client implementation."""

import atexit
import weakref
from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Union, cast

import httpx

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
    _class_persistent_clients: Dict[str, Union[httpx.Client, httpx.AsyncClient]] = {}

    def __init__(self, credentials: JiraCredentials):
        """Initialize the client with credentials.

        Args:
            credentials: JIRA authentication credentials.
        """
        self.credentials = credentials
        self._client: Any = None
        self._persistent_client: Union[httpx.Client, httpx.AsyncClient] | None = None
        self._async_mode = self._get_async_mode()  # Cache for performance
        self._client_key = self._get_client_key()

        # Register automatic cleanup
        self._finalizer = weakref.finalize(
            self, self._cleanup_instance_resources, self._client_key
        )

        # Register atexit cleanup if not already registered
        if not hasattr(self.__class__, "_atexit_registered"):
            atexit.register(self.__class__._cleanup_all_clients)
            setattr(self.__class__, "_atexit_registered", True)

    @abstractmethod
    def _get_client(self) -> Any:
        """Get the underlying HTTP client.

        Returns:
            The HTTP client instance (sync or async).
        """
        pass

    def _validate_client_type(
        self, client: Union[httpx.Client, httpx.AsyncClient]
    ) -> None:
        """Validate client type matches expected type.

        Args:
            client: The HTTP client instance to validate.

        Raises:
            AssertionError: If client type doesn't match expected type.
        """
        expected_type = self._get_client_type()
        assert isinstance(client, expected_type), f"Expected {expected_type.__name__}"

    def _get_persistent_client(self) -> Union[httpx.Client, httpx.AsyncClient]:
        """Generic template method for persistent client retrieval.

        This method eliminates code duplication by providing a single
        implementation that works for both sync and async clients through
        type parameter bounds and abstract configuration methods.

        Returns:
            Union[httpx.Client, httpx.AsyncClient]: The persistent HTTP client instance.
        """
        if self._client_key not in self._class_persistent_clients:
            client = JiraClientFactory.create_client(
                self.credentials, async_mode=self._async_mode
            )
            self._validate_client_type(client)
            self._class_persistent_clients[self._client_key] = client

        client = self._class_persistent_clients[self._client_key]
        self._validate_client_type(client)
        self._persistent_client = client
        return client

    @abstractmethod
    def _get_client_type(self) -> Type[Union[httpx.Client, httpx.AsyncClient]]:
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
        response_type: str = "dict",
    ) -> Any:
        """Make a request to the JIRA API using the provided HTTP call function.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash)
            params: Query parameters
            data: Request body data
            response_type: Expected response type ("dict" or "list")

        Returns:
            Response data as dict or list based on response_type parameter.
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

    def _handle_response_result(self, response: Any) -> Any:
        """Handle HTTP response and extract JSON data.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response as dict or list.
        """
        return self._handle_response(response)

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
        request_kwargs: Dict[str, Any] = {
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

    def _clean_none_values(self, data: Any) -> dict[str, Any] | list[Any] | None:
        """Recursively remove keys with falsy values from nested dictionaries and lists.

        Args:
            data: Data to clean

        Returns:
            Cleaned data with None values removed.
        """
        if data is None:
            return None
        elif isinstance(data, dict):
            return {k: self._clean_none_values(v) for k, v in data.items() if v}
        elif isinstance(data, list):
            return [self._clean_none_values(item) for item in data if item]
        else:
            return cast(dict[str, Any] | list[Any] | None, data)

    def _handle_response(
        self, response: Any
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        """Handle HTTP response and extract JSON data.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response as dict or list.

        Raises:
            ValueError: If response cannot be parsed as JSON.
        """
        try:
            return cast(Union[dict[str, Any], list[dict[str, Any]]], response.json())
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {e}")

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
        # Lazy import to avoid circular dependency at module level
        # This follows Python's official best practices for handling circular imports
        from jira2py import (
            JiraAPIError,
            JiraAuthenticationError,
            JiraConnectionError,
            JiraError,
            JiraNotFoundError,
            JiraRateLimitError,
            JiraValidationError,
        )

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
    def _cleanup_instance_resources(cls, client_key: str) -> None:
        """Cleanup resources for a specific client instance.

        Args:
            client_key: The key identifying the client to cleanup.
        """
        # This method is called by weakref.finalizer when an instance is garbage collected
        # We don't actually cleanup the shared client here, as other instances might still use it
        # The actual cleanup happens in _cleanup_all_clients at program exit
        pass

    @classmethod
    def _cleanup_all_clients(cls) -> None:
        """Cleanup all persistent clients at program exit."""
        for client_key, client in list(cls._class_persistent_clients.items()):
            try:
                if isinstance(client, httpx.AsyncClient):
                    # Handle async client
                    import asyncio

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create task but don't wait for it
                            loop.create_task(client.aclose())
                        else:
                            # Run in new event loop
                            asyncio.run(client.aclose())
                    except Exception:
                        # If asyncio fails, we can't do much more
                        pass
                elif isinstance(client, httpx.Client):
                    # Handle sync client
                    client.close()
            except Exception:
                # Ignore cleanup errors
                pass
        cls._class_persistent_clients.clear()
