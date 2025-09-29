"""Unified IssueFields API implementation using generic pattern."""

from typing import Any, cast, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientSync, JiraClientAsync
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
            "response_type": "list",
        }


class IssueFields(IssueFieldsBase[JiraClientSync]):
    """Synchronous IssueFields API implementation."""

    @validate_call
    def get_fields(self) -> list[dict[str, Any]]:
        """Returns system and custom issue fields
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            list[dict]: List of issue fields
        """
        request_config = self._get_fields_request_config()
        return cast(
            list[dict[str, Any]],
            self._client._request_jira(**request_config),
        )


class IssueFieldsAsync(IssueFieldsBase[JiraClientAsync]):
    """Asynchronous IssueFields API implementation."""

    @validate_call
    async def get_fields(self) -> list[dict[str, Any]]:
        """Returns system and custom issue fields
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            list[dict]: List of issue fields
        """
        request_config = self._get_fields_request_config()
        return cast(
            list[dict[str, Any]],
            await self._client._request_jira(**request_config),
        )
