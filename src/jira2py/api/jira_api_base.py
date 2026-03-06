"""Base class for Jira API facades."""

from typing import Any

from jira2py.client import JiraCredentials


class _JiraAPIBase:
    """Base class for Jira API facades.

    Provides shared initialization logic for sync and async facades.
    Subclasses must implement ``_create_client`` to return the appropriate
    client type.
    """

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
    ):
        """Initialize the Jira API facade.

        Args:
            url: Base URL of the JIRA instance.
            username: JIRA username.
            api_token: JIRA API token.
        """
        self._credentials = JiraCredentials.create(
            url=url, username=username, api_token=api_token
        )
        self._client = self._create_client()

    def _create_client(self) -> Any:
        """Create the appropriate client type.

        Subclasses must override this to return a sync or async client instance.
        """
        raise NotImplementedError

    @property
    def credentials(self) -> JiraCredentials:
        """Get the JIRA credentials."""
        return self._credentials
