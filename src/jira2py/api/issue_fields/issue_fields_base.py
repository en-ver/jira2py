"""Base class for IssueFields API - contains shared business logic."""

from typing import Any

from jira2py.client import JiraClientSync, JiraClientAsync


class IssueFieldsBase:
    """Base class for IssueFields API - contains shared business logic."""

    def __init__(self, client: JiraClientSync | JiraClientAsync) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client = client

    def _get_fields_request_config(self) -> dict[str, Any]:
        """Prepare request configuration for get_fields.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "field",
            "response_type": "list",
        }
