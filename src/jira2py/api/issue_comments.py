"""Unified IssueComments API implementation using generic pattern."""

from typing import Any, Literal, cast, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientSync, JiraClientAsync
from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class IssueCommentsBase(ApiBase[T]):
    """Base class for IssueComments API - contains shared business logic."""

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


class IssueCommentsAsync(IssueCommentsBase[JiraClientAsync]):
    """Asynchronous IssueComments API implementation."""

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


class IssueComments(IssueCommentsBase[JiraClientSync]):
    """Synchronous IssueComments API implementation."""

    @validate_call
    def get_comments(
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
            self._client._request_jira(**request_config),
        )
