"""Synchronous Issues API implementation."""

from typing import Any, cast

from pydantic import validate_call

from jira2py.client import JiraClientSync, JiraCredentials

from .issues import IssuesBase


class Issues(IssuesBase):
    """A class to interact with Jira's issues API (synchronous)."""

    def __init__(self, credentials: JiraCredentials | None = None):
        """Initialize the Issues client.

        Args:
            credentials: JIRA authentication credentials. If None, loads from environment.
        """
        super().__init__(JiraClientSync(credentials))

    @validate_call
    def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get details of a specific Jira issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id (str): The ID or key of the issue to retrieve.
            fields (str | None): A comma-separated list of fields to retrieve. Use "*all" for all fields.
            expand (str | None): A comma-separated list of properties to expand.
            extra_params (dict[str, Any] | None): Additional query parameters to include in the request.

        Returns:
            dict: A dictionary containing the issue details.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
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
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get

        Args:
            issue_id (str): The ID or key of the issue to get changelogs for.
            start_at (int): The index of the first item to return.
            max_results (int): The maximum number of results to return.
            extra_params (dict[str, Any] | None): Additional query parameters to include in the request.

        Returns:
            list[dict]: A list of dictionaries containing the changelog history for the issue.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
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
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put

        Args:
            issue_id (str): The ID or key of the issue to edit.
            fields (dict): A dictionary containing the fields to update. Each field should be specified with its ID or key and the new value.
            notify_users (bool, optional): Whether to send email notifications for the update. Defaults to True.
            return_issue (bool, optional): Whether to return the updated issue. Defaults to False.
            expand (str, optional): A comma-separated list of properties to expand.
            extra_params (dict[str, Any] | None): Additional query parameters to include in the request.
            extra_data (dict[str, Any] | None): Additional data parameters to include in the request body.

        Returns:
            dict: The updated issue details.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
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
