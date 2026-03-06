"""JIRA client factory implementation."""

import httpx

from .credentials import JiraCredentials


class JiraClientFactory:
    """Factory for creating HTTP clients for JIRA API interactions.

    This factory centralizes the creation and configuration of HTTP clients,
    eliminating code duplication between sync and async implementations.
    It handles all client configuration including connection pooling,
    timeouts, HTTP/2 settings, and authentication.

    Example:
        >>> credentials = JiraCredentials.create(url="https://example.atlassian.net", ...)
        >>> sync_client = JiraClientFactory.create_client(credentials, async_mode=False)
        >>> async_client = JiraClientFactory.create_client(credentials, async_mode=True)
    """

    # Default configuration constants
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CONNECT_TIMEOUT = 10.0
    DEFAULT_POOL_TIMEOUT = 5.0
    DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
    DEFAULT_MAX_CONNECTIONS = 50
    DEFAULT_KEEPALIVE_EXPIRY = 30.0

    @staticmethod
    def create_client(
        credentials: JiraCredentials, async_mode: bool = False
    ) -> httpx.Client | httpx.AsyncClient:
        """Create HTTP client instance with connection pooling.

        Args:
            credentials: JIRA authentication credentials.
            async_mode: Whether to create async client (True) or sync client (False)

        Returns:
            httpx.Client or httpx.AsyncClient instance
        """
        client_class = httpx.AsyncClient if async_mode else httpx.Client
        return client_class(
            base_url=f"{credentials.url}/rest/api/3",
            headers={"Accept": "application/json"},
            auth=httpx.BasicAuth(credentials.username, credentials.api_token),
            limits=httpx.Limits(
                max_keepalive_connections=JiraClientFactory.DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
                max_connections=JiraClientFactory.DEFAULT_MAX_CONNECTIONS,
                keepalive_expiry=JiraClientFactory.DEFAULT_KEEPALIVE_EXPIRY,
            ),
            timeout=httpx.Timeout(
                JiraClientFactory.DEFAULT_TIMEOUT,
                connect=JiraClientFactory.DEFAULT_CONNECT_TIMEOUT,
                pool=JiraClientFactory.DEFAULT_POOL_TIMEOUT,
            ),
            http2=True,  # Enable HTTP/2 for better performance
        )
