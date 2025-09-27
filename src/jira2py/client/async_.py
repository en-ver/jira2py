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
        self._persistent_client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the asynchronous HTTP client.

        Returns:
            httpx.AsyncClient: The asynchronous HTTP client instance.
        """
        return cast(httpx.AsyncClient, self._create_client(is_async=True))

    def _get_persistent_client(self) -> httpx.AsyncClient:
        """Get or create the persistent asynchronous HTTP client.

        Returns:
            httpx.AsyncClient: The persistent asynchronous HTTP client instance.
        """
        if self._persistent_client is None:
            self._persistent_client = cast(
                httpx.AsyncClient, self._create_client(is_async=True)
            )
        return self._persistent_client

    async def close(self) -> None:
        """Close both context and persistent client sessions."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._persistent_client:
            await self._persistent_client.aclose()
            self._persistent_client = None

    async def __aenter__(self) -> "JiraClientAsync":
        """Enter async context manager and create client session."""
        if self._client is not None:
            raise RuntimeError("Jira client session is already active")

        self._client = self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and cleanup client session."""
        if self._client:
            await self._client.aclose()
            self._client = None
