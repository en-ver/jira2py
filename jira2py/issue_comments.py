from .jira_base import JiraBase
from pydantic import validate_call
from typing import Literal


class IssueComments(JiraBase):

    @validate_call
    def get_comments(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 100,
        order_by: Literal["created", "-created", "updated", "-updated"] | None = None,
        expand: str | None = None,
    ) -> dict:
        """Returns all comments for an issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get

        Args:
            issue_id (str): The ID or key of the issue.
            start_at (int): The index of the first comment to return (0-based).
            max_results (int): The maximum number of comments to return.
            order_by (Literal["created", "-created", "updated", "-updated"] | None): The field to order the comments by.
            expand (str | None): A comma-separated list of fields to expand. This parameter accepts `renderedBody`, which returns the comment body rendered in HTML.

        Returns:
            dict: Comments and its metadata
        """
        kwargs = {
            "method": "GET",
            "context_path": f"issue/{issue_id}/comment",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
                "orderby": order_by,
                "expand": expand,
            },
        }

        return self._request_jira(**kwargs)
