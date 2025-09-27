"""Synchronous JIRA client implementation."""

from typing import Any, cast

import httpx

from .base import JiraClientBase
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
        self._persistent_client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client.

        Returns:
            httpx.Client: The HTTP client instance.
        """
        return cast(httpx.Client, self._create_client(is_async=False))

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
        if self._persistent_client:
            self._persistent_client.close()
            self._persistent_client = None

    def _get_persistent_client(self) -> httpx.Client:
        """Get or create the persistent HTTP client.

        Returns:
            httpx.Client: The persistent HTTP client instance.
        """
        if self._persistent_client is None:
            self._persistent_client = cast(
                httpx.Client, self._create_client(is_async=False)
            )
        return self._persistent_client

    def __enter__(self) -> "JiraClientSync":
        """Enter context manager and create client session."""
        if self._client is not None:
            raise RuntimeError("Jira client session is already active")

        self._client = self._get_client()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup client session."""
        if self._client:
            self._client.close()
            self._client = None
