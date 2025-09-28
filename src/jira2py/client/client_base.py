"""Base JIRA client implementation."""

import atexit
import weakref
from abc import ABC, abstractmethod
from typing import Any, Dict, Union, cast

import httpx

from .credentials import JiraCredentials


class JiraClientBase(ABC):
    """Abstract base class for JIRA clients.

    This class provides common functionality for both sync and async JIRA clients.
    It handles credentials management, request preparation, and response handling.

    Args:
        credentials: JIRA authentication credentials.
    """

    # Class-level storage for shared persistent clients
    _class_persistent_clients: Dict[str, Union[httpx.Client, httpx.AsyncClient]] = {}

    # Default configuration constants
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CONNECT_TIMEOUT = 10.0
    DEFAULT_POOL_TIMEOUT = 5.0
    DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
    DEFAULT_MAX_CONNECTIONS = 50
    DEFAULT_KEEPALIVE_EXPIRY = 30.0

    def __init__(self, credentials: JiraCredentials):
        """Initialize the client with credentials.

        Args:
            credentials: JIRA authentication credentials.
        """
        self.credentials = credentials
        self._client: Any = None
        self._client_key = self._get_client_key()

        # Register automatic cleanup
        self._finalizer = weakref.finalize(
            self, self._cleanup_instance_resources, self._client_key
        )

        # Register atexit cleanup if not already registered
        if not hasattr(self.__class__, "_atexit_registered"):
            atexit.register(self.__class__._cleanup_all_clients)
            setattr(self.__class__, "_atexit_registered", True)

    @classmethod
    def _create_client(
        cls, credentials: JiraCredentials, is_async: bool = False
    ) -> Union[httpx.Client, httpx.AsyncClient]:
        """Create HTTP client instance with connection pooling.

        Args:
            credentials: JIRA authentication credentials.
            is_async: Whether to create async client (True) or sync client (False)

        Returns:
            httpx.Client or httpx.AsyncClient instance
        """
        client_class = httpx.AsyncClient if is_async else httpx.Client
        return client_class(
            base_url=f"{credentials.url}/rest/api/3",
            headers={"Accept": "application/json"},
            auth=httpx.BasicAuth(
                credentials.username or "", credentials.api_token or ""
            ),
            limits=httpx.Limits(
                max_keepalive_connections=cls.DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
                max_connections=cls.DEFAULT_MAX_CONNECTIONS,
                keepalive_expiry=cls.DEFAULT_KEEPALIVE_EXPIRY,
            ),
            timeout=httpx.Timeout(
                cls.DEFAULT_TIMEOUT,
                connect=cls.DEFAULT_CONNECT_TIMEOUT,
                pool=cls.DEFAULT_POOL_TIMEOUT,
            ),
            http2=True,  # Enable HTTP/2 for better performance
        )

    @abstractmethod
    def _get_client(self) -> Any:
        """Get the underlying HTTP client.

        Returns:
            The HTTP client instance (sync or async).
        """
        pass

    @abstractmethod
    def _get_persistent_client(self) -> Any:
        """Get or create the persistent HTTP client.

        Returns:
            The persistent HTTP client instance (sync or async).
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

    def _handle_error(self, error: Exception) -> Exception:
        """Handle HTTP errors and convert them to appropriate exceptions.

        Args:
            error: Original error from HTTP client

        Returns:
            Appropriate exception for the error type.
        """
        # For now, just re-raise the original error
        # This can be enhanced later with custom exception types
        return error

    def _get_client_key(self) -> str:
        """Generate unique key for this credentials configuration.

        Returns:
            Unique string key for this client configuration.
        """
        return f"{self.credentials.url}:{self.credentials.username or 'anonymous'}"

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
