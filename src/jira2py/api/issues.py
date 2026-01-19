"""Unified Issues API implementation using generic pattern."""

from typing import Any, TypeVar, cast

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class IssuesBase(ApiBase[T]):
    """Base class for Issues API - contains shared business logic."""

    def _get_issue_request_config(
        self,
        issue_id: str,
        fields: str | None,
        expand: str | None,
        extra_params: dict[str, Any] | None,
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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


class Issues(IssuesBase[JiraClientSync]):
    """Synchronous Issues API implementation."""

    @validate_call
    def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific Jira issue.

        Retrieves the full issue details including all fields and metadata.
        Optionally specify which fields to return or which properties to expand.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id: The ID or key of the issue to retrieve (e.g., "PROJ-123").
            fields: A comma-separated list of fields to retrieve. Use "*all" for all fields.
                Defaults to None (returns default fields).
            expand: A comma-separated list of properties to expand (e.g., "renderedFields").
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the issue details including key, summary, status,
            description, and other requested fields. The exact structure depends on
            the fields parameter and Jira configuration.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> issue = api.issues.get_issue("PROJ-123")
            >>> print(issue["key"])
            'PROJ-123'
            >>> issue = api.issues.get_issue("PROJ-123", fields="summary,status")
        """
        request_config = self._get_issue_request_config(
            issue_id, fields, expand, extra_params
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )

    @validate_call
    def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get the changelogs for a Jira issue.

        Retrieves the audit history of changes made to an issue, including field changes,
        status transitions, and comment additions. Supports pagination.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get

        Args:
            issue_id: The ID or key of the issue to get changelogs for (e.g., "PROJ-123").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of results to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A list of dictionaries containing the changelog history for the issue.
            Each changelog entry includes the author, timestamp, and field changes.
            Returns an empty list if no changelogs exist.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> changelogs = api.issues.get_changelogs("PROJ-123", start_at=0, max_results=10)
            >>> len(changelogs)
            3
        """
        request_config = self._get_changelogs_request_config(
            issue_id, start_at, max_results, extra_params
        )
        return cast(
            list[dict[str, Any]],
            self._client._request_jira(**request_config),
        )

    @validate_call
    def edit_issue(
        self,
        issue_id: str,
        fields: dict[str, Any],
        notify_users: bool = True,
        return_issue: bool = False,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Edit a Jira issue.

        Updates one or more fields of an existing issue. By default, sends email
        notifications to watchers. Can optionally return the updated issue details.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put

        Args:
            issue_id: The ID or key of the issue to edit (e.g., "PROJ-123").
            fields: A dictionary containing the fields to update. Each field should be
                specified with its ID or key and the new value.
                Example: {"summary": "New summary", "priority": {"id": "3"}}.
            notify_users: Whether to send email notifications for the update.
                Defaults to True.
            return_issue: Whether to return the updated issue in the response.
                Defaults to False.
            expand: A comma-separated list of properties to expand in the response.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            The updated issue details if return_issue is True, otherwise an empty
            dictionary confirming the update was successful.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})
            >>> result = api.issues.edit_issue("PROJ-123", fields={"summary": "Updated"}, return_issue=True)
        """
        request_config = self._edit_issue_request_config(
            issue_id,
            fields,
            notify_users,
            return_issue,
            expand,
            extra_params,
            extra_data,
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )


class IssuesAsync(IssuesBase[JiraClientAsync]):
    """Asynchronous Issues API implementation."""

    @validate_call
    async def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific Jira issue (async version).

        Retrieves the full issue details including all fields and metadata.
        Optionally specify which fields to return or which properties to expand.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id: The ID or key of the issue to retrieve (e.g., "PROJ-123").
            fields: A comma-separated list of fields to retrieve. Use "*all" for all fields.
                Defaults to None (returns default fields).
            expand: A comma-separated list of properties to expand (e.g., "renderedFields").
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the issue details including key, summary, status,
            description, and other requested fields. The exact structure depends on
            the fields parameter and Jira configuration.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> issue = await api.issues.get_issue("PROJ-123")
            >>> print(issue["key"])
            'PROJ-123'
        """
        request_config = self._get_issue_request_config(
            issue_id, fields, expand, extra_params
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )

    @validate_call
    async def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get the changelogs for a Jira issue (async version).

        Retrieves the audit history of changes made to an issue, including field changes,
        status transitions, and comment additions. Supports pagination.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get

        Args:
            issue_id: The ID or key of the issue to get changelogs for (e.g., "PROJ-123").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of results to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A list of dictionaries containing the changelog history for the issue.
            Each changelog entry includes the author, timestamp, and field changes.
            Returns an empty list if no changelogs exist.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> changelogs = await api.issues.get_changelogs("PROJ-123", start_at=0, max_results=10)
            >>> len(changelogs)
            3
        """
        request_config = self._get_changelogs_request_config(
            issue_id, start_at, max_results, extra_params
        )
        return cast(
            list[dict[str, Any]],
            await self._client._request_jira(**request_config),
        )

    @validate_call
    async def edit_issue(
        self,
        issue_id: str,
        fields: dict[str, Any],
        notify_users: bool = True,
        return_issue: bool = False,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Edit a Jira issue (async version).

        Updates one or more fields of an existing issue. By default, sends email
        notifications to watchers. Can optionally return the updated issue details.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put

        Args:
            issue_id: The ID or key of the issue to edit (e.g., "PROJ-123").
            fields: A dictionary containing the fields to update. Each field should be
                specified with its ID or key and the new value.
                Example: {"summary": "New summary", "priority": {"id": "3"}}.
            notify_users: Whether to send email notifications for the update.
                Defaults to True.
            return_issue: Whether to return the updated issue in the response.
                Defaults to False.
            expand: A comma-separated list of properties to expand in the response.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            The updated issue details if return_issue is True, otherwise an empty
            dictionary confirming the update was successful.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = await api.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})
            >>> result = await api.issues.edit_issue("PROJ-123", fields={"summary": "Updated"}, return_issue=True)
        """
        request_config = self._edit_issue_request_config(
            issue_id,
            fields,
            notify_users,
            return_issue,
            expand,
            extra_params,
            extra_data,
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )
