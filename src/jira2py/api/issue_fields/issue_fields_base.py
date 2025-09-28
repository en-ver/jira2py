"""Base class for IssueFields API - contains shared business logic."""


class IssueFieldsBase:
    """Base class for IssueFields API - contains shared business logic."""

    def __init__(self, client):
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client = client

    def _get_fields_request_config(self):
        """Prepare request configuration for get_fields.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "field",
            "response_type": "list",
        }
