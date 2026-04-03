"""Issues API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class Issues(ApiBase):
    """Issues API — create, read, update issues and their metadata."""

    def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            fields: Comma-separated list of fields to retrieve. Use "*all" for all fields.
            expand: Comma-separated list of properties to expand (e.g., "renderedFields").
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Issue details including key, summary, status, and other requested fields.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}",
                params={"fields": fields, "expand": expand},
                extra_params=extra_params,
            )
        )

    def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the changelogs for a Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            start_at: Index of the first item to return (0-based).
            max_results: Maximum number of results to return.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Paginated response dict with keys: startAt, maxResults, total, isLast,
            and values (list of changelog entries with author, timestamp, and
            field changes).
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}/changelog",
                params={"startAt": start_at, "maxResults": max_results},
                extra_params=extra_params,
            )
        )

    def edit_issue(
        self,
        issue_id: str,
        fields: Mapping[str, Any],
        notify_users: bool = True,
        return_issue: bool = False,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Edit a Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            fields: Fields to update (e.g., {"summary": "New summary"}).
            notify_users: Whether to send email notifications.
            return_issue: Whether to return the updated issue in the response.
            expand: Comma-separated list of properties to expand.
            extra_params: Additional query parameters. Takes priority over named parameters.
            extra_data: Additional request body data. Takes priority over named data parameters.

        Returns:
            Updated issue details if return_issue is True, otherwise None.
        """
        result = self._client._request_jira(
            method="PUT",
            context_path=f"issue/{issue_id}",
            params={
                "notifyUsers": notify_users,
                "returnIssue": return_issue,
                "expand": expand,
            },
            data={"fields": fields},
            extra_params=extra_params,
            extra_data=extra_data,
        )
        if result is None:
            return None
        return self._as_dict(result)

    def get_edit_metadata(
        self,
        issue_id: str,
        override_screen_security: bool = False,
        override_editable_flag: bool = False,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the edit metadata for a Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-editmeta-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            override_screen_security: Override screen security.
            override_editable_flag: Override editable flag.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Edit metadata including available fields and their schemas.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}/editmeta",
                params={
                    "overrideScreenSecurity": override_screen_security,
                    "overrideEditableFlag": override_editable_flag,
                },
                extra_params=extra_params,
            )
        )

    def get_create_issue_types(
        self,
        project_id_or_key: str,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get issue types available for creating issues in a project.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ").
            start_at: Index of the first item to return (0-based).
            max_results: Maximum number of items to return.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Issue types available for the project.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/createmeta/{project_id_or_key}/issuetypes",
                params={"startAt": start_at, "maxResults": max_results},
                extra_params=extra_params,
            )
        )

    def get_create_fields(
        self,
        project_id_or_key: str,
        issue_type_id: str,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get fields available when creating an issue of a specific type.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-issuetypeid-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ").
            issue_type_id: The issue type ID (e.g., "10001").
            start_at: Index of the first item to return (0-based).
            max_results: Maximum number of items to return.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Fields available for creating the issue type.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/createmeta/{project_id_or_key}/issuetypes/{issue_type_id}",
                params={"startAt": start_at, "maxResults": max_results},
                extra_params=extra_params,
            )
        )

    def create_issue(
        self,
        fields: Mapping[str, Any],
        update_history: bool = False,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

        Args:
            fields: Issue fields. Must include project, issuetype, and summary.
            update_history: Whether to add the project to browse history.
            extra_params: Additional query parameters. Takes priority over named parameters.
            extra_data: Additional request body data. Takes priority over named data parameters.

        Returns:
            Created issue's id, key, and self URL.
        """
        return self._as_dict(
            self._client._request_jira(
                method="POST",
                context_path="issue",
                params={"updateHistory": update_history},
                data={"fields": fields},
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )
