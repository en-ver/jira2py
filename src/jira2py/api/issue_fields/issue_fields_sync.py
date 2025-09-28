"""Synchronous IssueFields API implementation."""

from typing import Any, cast

from pydantic import validate_call

from jira2py.client import JiraClientSync, JiraCredentials

from .issue_fields_base import IssueFieldsBase


class IssueFields(IssueFieldsBase):
    """A class to interact with Jira's issue fields API (synchronous)."""

    def __init__(self, credentials: JiraCredentials | None = None):
        """Initialize the IssueFields client.

        Args:
            credentials: JIRA authentication credentials. If None, loads from environment.
        """
        super().__init__(JiraClientSync(credentials))

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
