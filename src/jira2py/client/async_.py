"""Asynchronous JIRA client implementation."""

from typing import Any

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
        return httpx.AsyncClient(
            base_url=self.credentials.base_url,
            headers={"Accept": "application/json"},
            auth=httpx.BasicAuth(
                self.credentials.username or "", self.credentials.api_token or ""
            ),
        )

    def _get_persistent_client(self) -> httpx.AsyncClient:
        """Get or create the persistent asynchronous HTTP client.

        Returns:
            httpx.AsyncClient: The persistent asynchronous HTTP client instance.
        """
        if self._persistent_client is None:
            self._persistent_client = httpx.AsyncClient(
                base_url=self.credentials.base_url,
                headers={"Accept": "application/json"},
                auth=httpx.BasicAuth(
                    self.credentials.username or "", self.credentials.api_token or ""
                ),
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

    async def _make_request(
        self, client: httpx.AsyncClient, method: str, url: str, **kwargs: Any
    ) -> Any:
        """Make an asynchronous HTTP request.

        Args:
            client: The asynchronous HTTP client instance
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: Full URL for the request
            **kwargs: Additional request parameters

        Returns:
            HTTP response object
        """
        return await client.request(method, url, **kwargs)

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
