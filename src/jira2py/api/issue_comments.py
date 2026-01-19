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

        Retrieves comments for a specified issue with support for pagination
        and ordering. Can optionally expand rendered body for HTML content.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            start_at: The index of the first comment to return (0-based). Defaults to 0.
            max_results: The maximum number of comments to return. Defaults to 100.
            order_by: The field to order the comments by. Valid values are "created",
                "-created" (newest first), "updated", or "-updated" (most recently updated first).
                Defaults to None (chronological order).
            expand: A comma-separated list of fields to expand. Use "renderedBody" to get
                the comment body rendered in HTML. Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing comments and metadata including:
            - "startAt": The index of the first comment returned
            - "maxResults": The maximum number of results requested
            - "total": The total number of comments
            - "comments": List of comment dictionaries

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.comments.get_comments("PROJ-123", max_results=50)
            >>> len(result["comments"])
            25
        """
        request_config = self._get_comments_request_config(
            issue_id, start_at, max_results, order_by, expand, extra_params
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )


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
        """Returns all comments for an issue (async version).

        Retrieves comments for a specified issue with support for pagination
        and ordering. Can optionally expand rendered body for HTML content.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            start_at: The index of the first comment to return (0-based). Defaults to 0.
            max_results: The maximum number of comments to return. Defaults to 100.
            order_by: The field to order the comments by. Valid values are "created",
                "-created" (newest first), "updated", or "-updated" (most recently updated first).
                Defaults to None (chronological order).
            expand: A comma-separated list of fields to expand. Use "renderedBody" to get
                the comment body rendered in HTML. Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing comments and metadata including:
            - "startAt": The index of the first comment returned
            - "maxResults": The maximum number of results requested
            - "total": The total number of comments
            - "comments": List of comment dictionaries

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = await api.comments.get_comments("PROJ-123", max_results=50)
            >>> len(result["comments"])
            25
        """
        request_config = self._get_comments_request_config(
            issue_id, start_at, max_results, order_by, expand, extra_params
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )
