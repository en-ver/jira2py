"""Asynchronous JIRA client implementation."""

from typing import Any, Type, Union, cast

import httpx

from .client_base import JiraClientBase
from .credentials import JiraCredentials
from .factory import JiraClientFactory


class JiraClientAsync(JiraClientBase):
    """Asynchronous JIRA client.

    This client provides asynchronous HTTP requests to the JIRA API.
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
        """Initialize the asynchronous client.

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

    def _get_client(self) -> httpx.AsyncClient:
        """Get the asynchronous HTTP client (creates new one for one-time requests).

        Returns:
            httpx.AsyncClient: The asynchronous HTTP client instance.
        """
        return cast(
            httpx.AsyncClient,
            JiraClientFactory.create_client(self.credentials, async_mode=True),
        )

    def _get_client_type(self) -> Type[Union[httpx.Client, httpx.AsyncClient]]:
        """Return the async client type.

        Returns:
            Type[httpx.AsyncClient]: The httpx.AsyncClient type.
        """
        return httpx.AsyncClient

    def _get_async_mode(self) -> bool:
        """Return True for async client.

        Returns:
            bool: True for async client.
        """
        return True

    async def close(self) -> None:
        """Close the HTTP client references (doesn't close shared persistent client)."""
        if self._client:
            await self._client.aclose()
            self._client = None
        # Just clear the reference, don't close the shared persistent client
        self._persistent_client = None

    async def __aenter__(self) -> "JiraClientAsync":
        """Enter async context manager and borrow from persistent client session."""
        if self._client is not None:
            raise RuntimeError("Jira client session is already active")

        # Borrow from persistent client instead of creating new one
        self._client = self._get_persistent_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and clear client reference."""
        # Just clear the reference, don't close the persistent client
        self._client = None

    async def _request_jira(
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
        """Make an asynchronous request to the JIRA API.

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

        # Make asynchronous HTTP request
        response = await client.request(method, full_url, **request_kwargs)

        # Handle response using shared logic
        return self._handle_response_result(response)
