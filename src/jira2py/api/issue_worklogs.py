"""Issue Worklogs API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class IssueWorklogs(ApiBase):
    """Issue Worklogs API — list, add, update, and delete issue worklogs."""

    def get_worklogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get worklogs for an issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            start_at: Index of the first worklog to return (0-based).
            max_results: Maximum number of worklogs to return.
            extra_params: Additional query parameters. Takes priority over named
                parameters. Useful for Jira worklog parameters such as
                ``startedAfter``, ``startedBefore``, and ``expand``.

        Returns:
            Paginated worklogs with ``startAt``, ``maxResults``, ``total``, and
            ``worklogs``.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}/worklog",
                params={"startAt": start_at, "maxResults": max_results},
                extra_params=extra_params,
            )
        )

    def add_worklog(
        self,
        issue_id: str,
        time_spent: str,
        *,
        started: str | None = None,
        comment: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a worklog to an issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-post

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            time_spent: Work duration in Jira time-tracking format (e.g., "1h 30m").
            started: Optional worklog started timestamp in Jira-supported ISO format.
            comment: Optional worklog comment in Atlassian Document Format (ADF).
            extra_params: Additional query parameters. Takes priority over named
                parameters.
            extra_data: Additional request body data. Takes priority over named
                data parameters.

        Returns:
            Created worklog details.
        """
        data: dict[str, Any] = {"timeSpent": time_spent}
        if started is not None:
            data["started"] = started
        if comment is not None:
            data["comment"] = comment
        return self._as_dict(
            self._client._request_jira(
                method="POST",
                context_path=f"issue/{issue_id}/worklog",
                data=data,
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )

    def update_worklog(
        self,
        issue_id: str,
        worklog_id: str,
        *,
        time_spent: str | None = None,
        started: str | None = None,
        comment: Mapping[str, Any] | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing issue worklog.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-id-put

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            worklog_id: The Jira worklog ID.
            time_spent: Optional replacement work duration in Jira time-tracking
                format (e.g., "1h 30m").
            started: Optional replacement started timestamp in Jira-supported ISO
                format.
            comment: Optional replacement worklog comment in Atlassian Document
                Format (ADF).
            extra_params: Additional query parameters. Takes priority over named
                parameters.
            extra_data: Additional request body data. Takes priority over named
                data parameters.

        Returns:
            Updated worklog details.
        """
        data: dict[str, Any] = {}
        if time_spent is not None:
            data["timeSpent"] = time_spent
        if started is not None:
            data["started"] = started
        if comment is not None:
            data["comment"] = comment
        return self._as_dict(
            self._client._request_jira(
                method="PUT",
                context_path=f"issue/{issue_id}/worklog/{worklog_id}",
                data=data,
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )

    def delete_worklog(
        self,
        issue_id: str,
        worklog_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> None:
        """Delete an issue worklog.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-id-delete

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            worklog_id: The Jira worklog ID.
            extra_params: Additional query parameters. Takes priority over named
                parameters.
        """
        self._client._request_jira(
            method="DELETE",
            context_path=f"issue/{issue_id}/worklog/{worklog_id}",
            extra_params=extra_params,
        )
