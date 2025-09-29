"""Asynchronous IssueFields API implementation."""

from typing import Any, cast

from pydantic import validate_call

from jira2py.client import JiraClientAsync

from .issue_fields_base import IssueFieldsBase


class IssueFieldsAsync(IssueFieldsBase):
    """A class to interact with Jira's issue fields API (asynchronous)."""

    def __init__(self, client: JiraClientAsync):
        """Initialize the IssueFields client.

        Args:
            client: JIRA client instance.
        """
        super().__init__(client)

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
