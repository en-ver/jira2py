"""Issue Comments API implementation."""

from collections.abc import Mapping
from typing import Any, Literal

from .api_base import ApiBase


class IssueComments(ApiBase):
    """Issue Comments API — read and add comments on issues."""

    def get_comments(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 100,
        order_by: Literal["created", "-created", "updated", "-updated"] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get comments for an issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            start_at: Index of the first comment to return (0-based).
            max_results: Maximum number of comments to return.
            order_by: Order by "created", "-created", "updated", or "-updated".
            expand: Comma-separated fields to expand (e.g., "renderedBody").
            extra_params: Additional query parameters.

        Returns:
            Paginated comments with startAt, maxResults, total, and comments list.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}/comment",
                params={
                    "startAt": start_at,
                    "maxResults": max_results,
                    "orderby": order_by,
                    "expand": expand,
                },
                extra_params=extra_params,
            )
        )

    def add_comment(
        self,
        issue_id: str,
        body: Mapping[str, Any],
        visibility: Mapping[str, Any] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a comment to an issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            body: Comment body in Atlassian Document Format (ADF).
            visibility: Visibility restriction (e.g., {"type": "role", "value": "Administrators"}).
            expand: Comma-separated fields to expand (e.g., "renderedBody").
            extra_params: Additional query parameters.
            extra_data: Additional request body data.

        Returns:
            Created comment details including id, body, author, and created timestamp.
        """
        data: dict[str, Any] = {"body": body}
        if visibility is not None:
            data["visibility"] = visibility
        return self._as_dict(
            self._client._request_jira(
                method="POST",
                context_path=f"issue/{issue_id}/comment",
                params={"expand": expand},
                data=data,
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )
