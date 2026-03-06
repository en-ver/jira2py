"""Unified IssueFields API implementation using generic pattern."""

from typing import Any, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class IssueFieldsBase(ApiBase[T]):
    """Base class for IssueFields API - contains shared business logic."""

    def _get_fields_request_config(self) -> dict[str, Any]:
        """Prepare request configuration for get_fields.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "field",
        }


class IssueFields(IssueFieldsBase[JiraClientSync]):
    """Synchronous IssueFields API implementation."""

    @validate_call
    def get_fields(self) -> list[dict[str, Any]]:
        """Returns system and custom issue fields.

        Retrieves all fields available in the Jira instance, including both
        system fields (like summary, status, priority) and custom fields
        created by the administrator.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            A list of dictionaries, each representing a field with properties:
            - "id": The unique identifier for the field
            - "name": The human-readable name of the field
            - "custom": Whether this is a custom field (true/false)
            - "orderable": Whether the field can be used in ordering
            - "navigable": Whether the field can be used in navigation
            - "searchable": Whether the field can be searched in JQL
            - "schema": Detailed schema information about the field type

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> fields = api.fields.get_fields()
            >>> custom_fields = [f for f in fields if f.get("custom")]
            >>> len(custom_fields)
            15
        """
        request_config = self._get_fields_request_config()
        return self._as_list(self._client._request_jira(**request_config))


class IssueFieldsAsync(IssueFieldsBase[JiraClientAsync]):
    """Asynchronous IssueFields API implementation."""

    @validate_call
    async def get_fields(self) -> list[dict[str, Any]]:
        """Returns system and custom issue fields (async version).

        Retrieves all fields available in the Jira instance, including both
        system fields (like summary, status, priority) and custom fields
        created by the administrator.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            A list of dictionaries, each representing a field with properties:
            - "id": The unique identifier for the field
            - "name": The human-readable name of the field
            - "custom": Whether this is a custom field (true/false)
            - "orderable": Whether the field can be used in ordering
            - "navigable": Whether the field can be used in navigation
            - "searchable": Whether the field can be searched in JQL
            - "schema": Detailed schema information about the field type

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> fields = await api.fields.get_fields()
            >>> custom_fields = [f for f in fields if f.get("custom")]
            >>> len(custom_fields)
            15
        """
        request_config = self._get_fields_request_config()
        return self._as_list(await self._client._request_jira(**request_config))
