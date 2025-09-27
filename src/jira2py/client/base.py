"""Base JIRA client implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Union, cast

from .credentials import JiraCredentials


class JiraClientBase(ABC):
    """Abstract base class for JIRA clients.

    This class provides common functionality for both sync and async JIRA clients.
    It handles credentials management, request preparation, and response handling.

    Args:
        credentials: JIRA authentication credentials.
    """

    def __init__(self, credentials: JiraCredentials):
        """Initialize the client with credentials.

        Args:
            credentials: JIRA authentication credentials.
        """
        self.credentials = credentials
        self._client: Any = None

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

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        response_type: str = "dict",
    ) -> Any:
        """Make a request to the JIRA API using template method pattern.

        This method contains all shared logic for making HTTP requests to JIRA.
        The actual HTTP request is delegated to the _make_request hook method.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash)
            params: Query parameters
            data: Request body data
            response_type: Expected response type ("dict" or "list")

        Returns:
            Response data as dict or list based on response_type parameter.
        """
        # Prepare request parameters (shared logic)
        method, full_url, request_kwargs = self._prepare_request(
            method, context_path, params, data
        )

        # Use context client if available, otherwise get persistent client
        client = (
            self._client if self._client is not None else self._get_persistent_client()
        )

        # Make HTTP request (hook method - implemented by subclasses)
        response = self._make_request(client, method, full_url, **request_kwargs)

        # Handle response (shared logic)
        return self._handle_response(response)

    @abstractmethod
    def _make_request(self, client: Any, method: str, url: str, **kwargs: Any) -> Any:
        """Make the actual HTTP request (hook method).

        This method is implemented by sync and async subclasses to handle
        their specific HTTP request patterns.

        Args:
            client: The HTTP client instance (sync or async)
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Full URL for the request
            **kwargs: Additional request parameters

        Returns:
            HTTP response object
        """
        pass

    def _prepare_request(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
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
        # Clean up params and data to remove None values
        clean_params = self._clean_none_values(params)
        clean_data = self._clean_none_values(data)

        # Construct full URL
        full_url = f"{self.credentials.base_url}/{context_path.lstrip('/')}"

        # Prepare request kwargs
        request_kwargs: Dict[str, Any] = {
            "headers": {"Accept": "application/json"},
        }

        if clean_params:
            request_kwargs["params"] = clean_params

        if clean_data:
            request_kwargs["json"] = clean_data

        return method, full_url, request_kwargs

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
