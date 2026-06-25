"""Issue Worklogs API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class IssueWorklogs(ApiBase):
    """Issue Worklogs API — read worklogs on issues."""

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
