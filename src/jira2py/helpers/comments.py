"""Grouped comment helper operations for jira2py."""

from __future__ import annotations

from typing import Literal

from jira2py.api import JiraAPI

from ._adf import markdown_to_adf
from ._text import format_comment
from ._validation import require_non_empty_string
from .errors import JiraHelperOperationError
from .models import CommentPage, JiraComment
from .results import HelperResult


class CommentHelpers:
    """High-level grouped helpers for Jira comments."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def list(
        self,
        issue_key: str,
        *,
        start_at: int = 0,
        max_results: int = 50,
        order_by: Literal["created", "-created", "updated", "-updated"] = "created",
    ) -> HelperResult:
        """List comments on a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        limit = min(max_results, 100)

        try:
            data = self.api.comments.get_comments(
                issue_id=issue_key,
                start_at=start_at,
                max_results=limit,
                order_by=order_by,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch comments for {issue_key}: {exc}"
            ) from exc

        page = CommentPage.model_validate(data)
        actual_start = page.startAt
        if not page.comments:
            if actual_start > 0:
                text = f"No comments at offset {actual_start} (total: {page.total})"
            else:
                text = f"No comments on {issue_key}"
            return HelperResult.with_data(text, data)

        lines: list[str] = []
        if page.total > len(page.comments) or actual_start > 0:
            end = actual_start + len(page.comments)
            lines.append(
                f"Comments on {issue_key}: showing {actual_start + 1}–{end} of {page.total}\n"
            )
        else:
            lines.append(f"Comments on {issue_key}: {page.total} total\n")

        for comment in page.comments:
            lines.append(format_comment(comment))
            lines.append("")

        if actual_start + len(page.comments) < page.total:
            next_start = actual_start + len(page.comments)
            lines.append(
                "--- More comments available. "
                f"Use start_at={next_start} to fetch the next page. ---"
            )

        return HelperResult.with_data("\n".join(lines), data)

    def add(self, issue_key: str, body: str) -> HelperResult:
        """Add a comment to a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        body = require_non_empty_string(body, field_name="body")

        try:
            data = self.api.comments.add_comment(
                issue_id=issue_key,
                body=markdown_to_adf(body),
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to add comment to {issue_key}: {exc}"
            ) from exc

        text = f"Added comment to {issue_key}\nURL: {self.api.credentials.url}/browse/{issue_key}"
        return HelperResult.with_data(text, data)

    def update(self, issue_key: str, comment_id: str, body: str) -> HelperResult:
        """Update an existing Jira issue comment."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        comment_id = require_non_empty_string(comment_id, field_name="comment_id")
        body = require_non_empty_string(body, field_name="body")

        try:
            data = self.api.comments.update_comment(
                issue_id=issue_key,
                comment_id=comment_id,
                body=markdown_to_adf(body),
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to update comment {comment_id} on {issue_key}: {exc}"
            ) from exc

        comment = JiraComment.model_validate(data)
        text = (
            f"Updated comment {comment_id} on {issue_key}\n"
            f"URL: {self.api.credentials.url}/browse/{issue_key}\n\n"
            f"{format_comment(comment)}"
        )
        return HelperResult.with_data(text, data)

    def delete(self, issue_key: str, comment_id: str) -> HelperResult:
        """Delete a Jira issue comment."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        comment_id = require_non_empty_string(comment_id, field_name="comment_id")

        try:
            self.api.comments.delete_comment(
                issue_id=issue_key,
                comment_id=comment_id,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to delete comment {comment_id} from {issue_key}: {exc}"
            ) from exc

        data = {
            "status": "deleted",
            "issue_key": issue_key,
            "comment_id": comment_id,
        }
        text = (
            f"Deleted comment {comment_id} from {issue_key}\n"
            f"URL: {self.api.credentials.url}/browse/{issue_key}"
        )
        return HelperResult.with_data(text, data)


__all__ = ["CommentHelpers"]
