"""Unified IssueComments API implementation using generic pattern."""

from collections.abc import Mapping
from typing import Any, Literal, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

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
        extra_params: Mapping[str, Any] | None,
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
        }

    def _add_comment_request_config(
        self,
        issue_id: str,
        body: Mapping[str, Any],
        visibility: Mapping[str, Any] | None,
        expand: str | None,
        extra_params: Mapping[str, Any] | None,
        extra_data: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for add_comment.

        Args:
            issue_id: The ID or key of the issue.
            body: The comment body in ADF format.
            visibility: Optional visibility restriction for the comment.
            expand: A comma-separated list of fields to expand.
            extra_params: Additional query parameters to include in the request.
            extra_data: Additional data parameters to include in the request body.

        Returns:
            Dictionary with request configuration.
        """
        data: dict[str, Any] = {"body": body}
        if visibility is not None:
            data["visibility"] = visibility
        return {
            "method": "POST",
            "context_path": f"issue/{issue_id}/comment",
            "params": {
                "expand": expand,
            },
            "data": data,
            "extra_params": extra_params,
            "extra_data": extra_data,
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
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def add_comment(
        self,
        issue_id: str,
        body: Mapping[str, Any],
        visibility: Mapping[str, Any] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a comment to a Jira issue.

        Creates a new comment on an issue. The comment body must be in Atlassian
        Document Format (ADF). Optionally restrict visibility to a role or group.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            body: The comment body in ADF format.
            visibility: Optional visibility restriction. Example:
                {"type": "role", "value": "Administrators"}.
                Defaults to None (visible to all).
            expand: A comma-separated list of fields to expand. Use "renderedBody"
                to get the comment rendered in HTML. Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the created comment details including id,
            body, author, created timestamp, and visibility.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> comment = api.comments.add_comment("PROJ-123", body=adf_body)
            >>> print(comment["id"])
            '10000'
        """
        request_config = self._add_comment_request_config(
            issue_id, body, visibility, expand, extra_params, extra_data
        )
        return self._as_dict(self._client._request_jira(**request_config))


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
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def add_comment(
        self,
        issue_id: str,
        body: Mapping[str, Any],
        visibility: Mapping[str, Any] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a comment to a Jira issue (async version).

        Creates a new comment on an issue. The comment body must be in Atlassian
        Document Format (ADF). Optionally restrict visibility to a role or group.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            body: The comment body in ADF format.
            visibility: Optional visibility restriction. Example:
                {"type": "role", "value": "Administrators"}.
                Defaults to None (visible to all).
            expand: A comma-separated list of fields to expand. Use "renderedBody"
                to get the comment rendered in HTML. Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the created comment details including id,
            body, author, created timestamp, and visibility.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> comment = await api.comments.add_comment("PROJ-123", body=adf_body)
            >>> print(comment["id"])
            '10000'
        """
        request_config = self._add_comment_request_config(
            issue_id, body, visibility, expand, extra_params, extra_data
        )
        return self._as_dict(await self._client._request_jira(**request_config))
