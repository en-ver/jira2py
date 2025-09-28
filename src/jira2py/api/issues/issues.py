"""Base class for Issues API - contains shared business logic."""

from typing import Any


class IssuesBase:
    """Base class for Issues API - contains shared business logic."""

    def __init__(self, client):
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client = client

    def _get_issue_request_config(
        self,
        issue_id: str,
        fields: str | None,
        expand: str | None,
        extra_params: dict[str, Any] | None,
    ):
        """Prepare request configuration for get_issue.

        Args:
            issue_id: The ID or key of the issue to retrieve.
            fields: A comma-separated list of fields to retrieve.
            expand: A comma-separated list of properties to expand.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/{issue_id}",
            "params": {
                "fields": fields,
                "expand": expand,
            },
            "extra_params": extra_params,
            "response_type": "dict",
        }

    def _get_changelogs_request_config(
        self,
        issue_id: str,
        start_at: int,
        max_results: int,
        extra_params: dict[str, Any] | None,
    ):
        """Prepare request configuration for get_changelogs.

        Args:
            issue_id: The ID or key of the issue to get changelogs for.
            start_at: The index of the first item to return.
            max_results: The maximum number of results to return.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/{issue_id}/changelog",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
            },
            "extra_params": extra_params,
            "response_type": "list",
        }

    def _edit_issue_request_config(
        self,
        issue_id: str,
        fields: dict[str, Any],
        notify_users: bool,
        return_issue: bool,
        expand: str | None,
        extra_params: dict[str, Any] | None,
        extra_data: dict[str, Any] | None,
    ):
        """Prepare request configuration for edit_issue.

        Args:
            issue_id: The ID or key of the issue to edit.
            fields: A dictionary containing the fields to update.
            notify_users: Whether to send email notifications for the update.
            return_issue: Whether to return the updated issue.
            expand: A comma-separated list of properties to expand.
            extra_params: Additional query parameters to include in the request.
            extra_data: Additional data parameters to include in the request body.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "PUT",
            "context_path": f"issue/{issue_id}",
            "params": {
                "notifyUsers": notify_users,
                "returnIssue": return_issue,
                "expand": expand,
            },
            "data": {
                "fields": fields,
            },
            "extra_params": extra_params,
            "extra_data": extra_data,
            "response_type": "dict",
        }
