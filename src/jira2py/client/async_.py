"""Asynchronous JIRA client implementation."""

from typing import Any, cast

import httpx

from .base import JiraClientBase
from .credentials import JiraCredentials


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
        # Instance-level reference to shared persistent client
        self._persistent_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the asynchronous HTTP client (creates new one for one-time requests).

        Returns:
            httpx.AsyncClient: The asynchronous HTTP client instance.
        """
        return cast(
            httpx.AsyncClient, self._create_client(self.credentials, is_async=True)
        )

    def _get_persistent_client(self) -> httpx.AsyncClient:
        """Get or create the shared persistent asynchronous HTTP client.

        Returns:
            httpx.AsyncClient: The shared persistent asynchronous HTTP client instance.
        """
        # Use class-level shared client instead of instance-level
        if self._client_key not in self._class_persistent_clients:
            client = self._create_client(self.credentials, is_async=True)
            assert isinstance(client, httpx.AsyncClient), (
                "Expected httpx.AsyncClient for async client"
            )
            self._class_persistent_clients[self._client_key] = client
        client = self._class_persistent_clients[self._client_key]
        assert isinstance(client, httpx.AsyncClient), (
            "Expected httpx.AsyncClient in persistent clients"
        )
        self._persistent_client = client
        return client

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
