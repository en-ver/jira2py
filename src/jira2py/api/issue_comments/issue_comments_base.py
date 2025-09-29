"""Base class for IssueComments API - contains shared business logic."""

from typing import Any, Literal

from jira2py.client import JiraClientSync, JiraClientAsync


class IssueCommentsBase:
    """Base class for IssueComments API - contains shared business logic."""

    def __init__(self, client: JiraClientSync | JiraClientAsync) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client = client

    def _get_comments_request_config(
        self,
        issue_id: str,
        start_at: int,
        max_results: int,
        order_by: Literal["created", "-created", "updated", "-updated"] | None,
        expand: str | None,
        extra_params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for get_comments.

        Args:
            issue_id: The ID or key of the issue.
            start_at: The index of the first comment to return (0-based).
            max_results: The maximum number of comments to return.
            order_by: The field to order the comments by.
            expand: A comma-separated list of fields to expand.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/{issue_id}/comment",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
                "orderby": order_by,
                "expand": expand,
            },
            "extra_params": extra_params,
            "response_type": "dict",
        }
