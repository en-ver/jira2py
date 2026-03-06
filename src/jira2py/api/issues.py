"""Unified Issues API implementation using generic pattern."""

from collections.abc import Mapping
from typing import Any, TypeVar

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
        extra_params: Mapping[str, Any] | None,
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
        }

    def _get_changelogs_request_config(
        self,
        issue_id: str,
        start_at: int,
        max_results: int,
        extra_params: Mapping[str, Any] | None,
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
        }

    def _edit_issue_request_config(
        self,
        issue_id: str,
        fields: Mapping[str, Any],
        notify_users: bool,
        return_issue: bool,
        expand: str | None,
        extra_params: Mapping[str, Any] | None,
        extra_data: Mapping[str, Any] | None,
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
        }

    def _get_edit_metadata_request_config(
        self,
        issue_id: str,
        override_screen_security: bool,
        override_editable_flag: bool,
        extra_params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for get_edit_metadata.

        Args:
            issue_id: The ID or key of the issue.
            override_screen_security: Whether screen security should be overridden.
            override_editable_flag: Whether the editable flag should be overridden.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/{issue_id}/editmeta",
            "params": {
                "overrideScreenSecurity": override_screen_security,
                "overrideEditableFlag": override_editable_flag,
            },
            "extra_params": extra_params,
        }

    def _get_create_issue_types_request_config(
        self,
        project_id_or_key: str,
        start_at: int,
        max_results: int,
        extra_params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for get_create_issue_types.

        Args:
            project_id_or_key: The project ID or key.
            start_at: The index of the first item to return (0-based).
            max_results: The maximum number of items to return.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/createmeta/{project_id_or_key}/issuetypes",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
            },
            "extra_params": extra_params,
        }

    def _get_create_fields_request_config(
        self,
        project_id_or_key: str,
        issue_type_id: str,
        start_at: int,
        max_results: int,
        extra_params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for get_create_fields.

        Args:
            project_id_or_key: The project ID or key.
            issue_type_id: The issue type ID.
            start_at: The index of the first item to return (0-based).
            max_results: The maximum number of items to return.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"issue/createmeta/{project_id_or_key}/issuetypes/{issue_type_id}",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
            },
            "extra_params": extra_params,
        }

    def _create_issue_request_config(
        self,
        fields: Mapping[str, Any],
        update_history: bool,
        extra_params: Mapping[str, Any] | None,
        extra_data: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for create_issue.

        Args:
            fields: A dictionary containing the issue fields.
            update_history: Whether to add the project to the user's browse history.
            extra_params: Additional query parameters to include in the request.
            extra_data: Additional data parameters to include in the request body.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "POST",
            "context_path": "issue",
            "params": {
                "updateHistory": update_history,
            },
            "data": {
                "fields": fields,
            },
            "extra_params": extra_params,
            "extra_data": extra_data,
        }


class Issues(IssuesBase[JiraClientSync]):
    """Synchronous Issues API implementation."""

    @validate_call
    def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_list(self._client._request_jira(**request_config))

    @validate_call
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
            The updated issue details if return_issue is True, otherwise None
            (Jira returns 204 No Content on successful edit).

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> api.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})
            >>> issue = api.issues.edit_issue("PROJ-123", fields={"summary": "Updated"}, return_issue=True)
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
        result = self._client._request_jira(**request_config)
        if result is None:
            return None
        return self._as_dict(result)

    @validate_call
    def get_edit_metadata(
        self,
        issue_id: str,
        override_screen_security: bool = False,
        override_editable_flag: bool = False,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the edit metadata for a Jira issue.

        Returns the metadata describing the fields available for editing on the issue,
        including field types, allowed values, and whether fields are required.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-editmeta-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            override_screen_security: Whether screen security should be overridden.
                Defaults to False.
            override_editable_flag: Whether the editable flag should be overridden.
                Defaults to False.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the edit metadata for the issue, including
            available fields and their schemas.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> meta = api.issues.get_edit_metadata("PROJ-123")
            >>> list(meta["fields"].keys())
            ['summary', 'description', 'priority', ...]
        """
        request_config = self._get_edit_metadata_request_config(
            issue_id, override_screen_security, override_editable_flag, extra_params
        )
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def get_create_issue_types(
        self,
        project_id_or_key: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the issue types available for creating issues in a project.

        Returns the issue types that can be used when creating issues in the specified
        project, including their IDs, names, and descriptions.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ" or "10000").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of items to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the issue types available for the project.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the project is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> types = api.issues.get_create_issue_types("PROJ")
            >>> [t["name"] for t in types["values"]]
            ['Bug', 'Story', 'Task', ...]
        """
        request_config = self._get_create_issue_types_request_config(
            project_id_or_key, start_at, max_results, extra_params
        )
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def get_create_fields(
        self,
        project_id_or_key: str,
        issue_type_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the fields available when creating an issue of a specific type in a project.

        Returns the fields and their metadata that can be set when creating an issue
        of the specified type in the specified project.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-issuetypeid-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ" or "10000").
            issue_type_id: The issue type ID (e.g., "10001").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of items to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the fields available for creating the issue type.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the project or issue type is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> fields = api.issues.get_create_fields("PROJ", "10001")
            >>> list(fields["values"])
            [{'fieldId': 'summary', ...}, {'fieldId': 'description', ...}]
        """
        request_config = self._get_create_fields_request_config(
            project_id_or_key, issue_type_id, start_at, max_results, extra_params
        )
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def create_issue(
        self,
        fields: Mapping[str, Any],
        update_history: bool = False,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Jira issue.

        Creates a new issue with the specified fields. At minimum, the project,
        issue type, and summary fields are required.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

        Args:
            fields: A dictionary containing the issue fields. Must include at minimum:
                - "project": {"id": "..."} or {"key": "..."}
                - "issuetype": {"id": "..."}
                - "summary": "Issue summary"
                Example: {"project": {"key": "PROJ"}, "issuetype": {"id": "10001"},
                          "summary": "New bug"}
            update_history: Whether to add the project to the user's browse history.
                Defaults to False.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the created issue's id, key, and self URL.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.issues.create_issue(fields={
            ...     "project": {"key": "PROJ"},
            ...     "issuetype": {"id": "10001"},
            ...     "summary": "New bug report",
            ... })
            >>> print(result["key"])
            'PROJ-456'
        """
        request_config = self._create_issue_request_config(
            fields, update_history, extra_params, extra_data
        )
        return self._as_dict(self._client._request_jira(**request_config))


class IssuesAsync(IssuesBase[JiraClientAsync]):
    """Asynchronous Issues API implementation."""

    @validate_call
    async def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
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
        return self._as_list(await self._client._request_jira(**request_config))

    @validate_call
    async def edit_issue(
        self,
        issue_id: str,
        fields: Mapping[str, Any],
        notify_users: bool = True,
        return_issue: bool = False,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
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
            The updated issue details if return_issue is True, otherwise None
            (Jira returns 204 No Content on successful edit).

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> api.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})
            >>> issue = await api.issues.edit_issue("PROJ-123", fields={"summary": "Updated"}, return_issue=True)
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
        result = await self._client._request_jira(**request_config)
        if result is None:
            return None
        return self._as_dict(result)

    @validate_call
    async def get_edit_metadata(
        self,
        issue_id: str,
        override_screen_security: bool = False,
        override_editable_flag: bool = False,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the edit metadata for a Jira issue (async version).

        Returns the metadata describing the fields available for editing on the issue,
        including field types, allowed values, and whether fields are required.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-editmeta-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            override_screen_security: Whether screen security should be overridden.
                Defaults to False.
            override_editable_flag: Whether the editable flag should be overridden.
                Defaults to False.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the edit metadata for the issue, including
            available fields and their schemas.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the issue is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> meta = await api.issues.get_edit_metadata("PROJ-123")
            >>> list(meta["fields"].keys())
            ['summary', 'description', 'priority', ...]
        """
        request_config = self._get_edit_metadata_request_config(
            issue_id, override_screen_security, override_editable_flag, extra_params
        )
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def get_create_issue_types(
        self,
        project_id_or_key: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the issue types available for creating issues in a project (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ" or "10000").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of items to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the issue types available for the project.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the project is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> types = await api.issues.get_create_issue_types("PROJ")
        """
        request_config = self._get_create_issue_types_request_config(
            project_id_or_key, start_at, max_results, extra_params
        )
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def get_create_fields(
        self,
        project_id_or_key: str,
        issue_type_id: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get the fields available when creating an issue of a specific type (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-issuetypeid-get

        Args:
            project_id_or_key: The project ID or key (e.g., "PROJ" or "10000").
            issue_type_id: The issue type ID (e.g., "10001").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of items to return. Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the fields available for creating the issue type.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the project or issue type is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> fields = await api.issues.get_create_fields("PROJ", "10001")
        """
        request_config = self._get_create_fields_request_config(
            project_id_or_key, issue_type_id, start_at, max_results, extra_params
        )
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def create_issue(
        self,
        fields: Mapping[str, Any],
        update_history: bool = False,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Jira issue (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post

        Args:
            fields: A dictionary containing the issue fields. Must include at minimum:
                - "project": {"id": "..."} or {"key": "..."}
                - "issuetype": {"id": "..."}
                - "summary": "Issue summary"
            update_history: Whether to add the project to the user's browse history.
                Defaults to False.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the created issue's id, key, and self URL.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If the field data is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = await api.issues.create_issue(fields={
            ...     "project": {"key": "PROJ"},
            ...     "issuetype": {"id": "10001"},
            ...     "summary": "New bug report",
            ... })
        """
        request_config = self._create_issue_request_config(
            fields, update_history, extra_params, extra_data
        )
        return self._as_dict(await self._client._request_jira(**request_config))
