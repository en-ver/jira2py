"""Synchronous JIRA client implementation."""

from typing import Any, cast

import httpx

from .client_base import JiraClientBase
from .credentials import JiraCredentials


class JiraClientSync(JiraClientBase):
    """Synchronous JIRA client.

    This client provides synchronous HTTP requests to the JIRA API.
    It supports both context manager usage and persistent client sessions.

    Args:
        credentials: JIRA authentication credentials.
    """

    def __init__(
        self,
        credentials: JiraCredentials | None = None,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
    ):
        """Initialize the synchronous client.

        Args:
            credentials: JIRA authentication credentials. If None, credentials will be
                created from the provided parameters or environment variables.
            url: Base URL of the JIRA instance. Only used if credentials is None.
            username: JIRA username. Only used if credentials is None.
            api_token: JIRA API token. Only used if credentials is None.
        """
        if credentials is None:
            credentials = JiraCredentials(
                url=url, username=username, api_token=api_token
            )
        super().__init__(credentials)
        # Instance-level reference to shared persistent client
        self._persistent_client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get the HTTP client (creates new one for one-time requests).

        Returns:
            httpx.Client: The HTTP client instance.
        """
        return cast(httpx.Client, self._create_client(self.credentials, is_async=False))

    def close(self) -> None:
        """Close the HTTP client references (doesn't close shared persistent client)."""
        if self._client:
            self._client.close()
            self._client = None
        # Just clear the reference, don't close the shared persistent client
        self._persistent_client = None

    def _get_persistent_client(self) -> httpx.Client:
        """Get or create the shared persistent HTTP client.

        Returns:
            httpx.Client: The shared persistent HTTP client instance.
        """
        # Use class-level shared client instead of instance-level
        if self._client_key not in self._class_persistent_clients:
            client = self._create_client(self.credentials, is_async=False)
            assert isinstance(client, httpx.Client), (
                "Expected httpx.Client for sync client"
            )
            self._class_persistent_clients[self._client_key] = client
        client = self._class_persistent_clients[self._client_key]
        assert isinstance(client, httpx.Client), (
            "Expected httpx.Client in persistent clients"
        )
        self._persistent_client = client
        return client

    def __enter__(self) -> "JiraClientSync":
        """Enter context manager and borrow from persistent client session."""
        if self._client is not None:
            raise RuntimeError("Jira client session is already active")

        # Borrow from persistent client instead of creating new one
        self._client = self._get_persistent_client()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and clear client reference."""
        # Just clear the reference, don't close the persistent client
        self._client = None

    def _request_jira(
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
        """Make a synchronous request to the JIRA API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            context_path: API endpoint path (without leading slash)
            params: Query parameters
            data: Request body data
            response_type: Expected response type ("dict" or "list")

        Returns:
            Response data as dict or list based on response_type parameter.
        """
        # Get prepared request components from base
        client, method, full_url, request_kwargs = self._request_jira_base(
            method,
            context_path,
            params,
            data,
            extra_params=extra_params,
            extra_data=extra_data,
            response_type=response_type,
        )

        # Make synchronous HTTP request
        response = client.request(method, full_url, **request_kwargs)

        # Handle response using shared logic
        return self._handle_response_result(response)
