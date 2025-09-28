"""Asynchronous IssueComments API implementation."""

from typing import Any, Literal, cast

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraCredentials

from .issue_comments_base import IssueCommentsBase


class IssueCommentsAsync(IssueCommentsBase):
    """A class to interact with Jira's issue comments API (asynchronous)."""

    def __init__(self, credentials: JiraCredentials | None = None):
        """Initialize the IssueComments client.

        Args:
            credentials: JIRA authentication credentials. If None, loads from environment.
        """
        super().__init__(JiraClientAsync(credentials))

    @validate_call
    async def get_comments(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 100,
        order_by: Literal["created", "-created", "updated", "-updated"] | None = None,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Returns all comments for an issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get

        Args:
            issue_id (str): The ID or key of the issue.
            start_at (int): The index of the first comment to return (0-based).
            max_results (int): The maximum number of comments to return.
            order_by (Literal["created", "-created", "updated", "-updated"] | None): The field to order the comments by.
            expand (str | None): A comma-separated list of fields to expand. This parameter accepts `renderedBody`, which returns the comment body rendered in HTML.
            extra_params (dict[str, Any] | None): Additional query parameters to include in the request.

        Returns:
            dict: Comments and its metadata
        """
        request_config = self._get_comments_request_config(
            issue_id, start_at, max_results, order_by, expand, extra_params
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )
