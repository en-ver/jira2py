from typing import Any

from pydantic import validate_call

from .jira_base import JiraBase


class Issues(JiraBase):
    """A class to interact with Jira's issues API."""

    @validate_call
    def get_issue(
        self,
        issue_id: str,
        fields: str | None = None,
        fields_by_keys: bool = False,
        expand: str | None = None,
        properties: list[str] | None = None,
        update_history: bool = False,
        fail_fast: bool = False,
    ) -> dict:
        """Get details of a specific Jira issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id (str): The ID or key of the issue to retrieve.
            fields (str | None): A comma-separated list of fields to retrieve. Use "*all" for all fields.
            fields_by_keys (bool): Whether fields are referenced by keys instead of IDs.
            expand (str | None): A comma-separated list of properties to expand.
            properties (list[str] | None): A list of properties to include in the response.
            update_history (bool): Whether to update the issue history.
            fail_fast (bool): Whether to fail fast if the issue does not exist.

        Returns:
            dict: A dictionary containing the issue details.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """

        return self._request_jira(
            method="GET",
            context_path=f"issue/{issue_id}",
            params={
                "fields": fields,
                "fieldsByKeys": fields_by_keys,
                "expand": expand,
                "properties": properties,
                "updateHistory": update_history,
                "failFast": fail_fast,
            },
            response_type=dict,
        )

    @validate_call
    def get_changelogs(
        self,
        issue_id: str,
        start_at: int = 0,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Get the changelogs for a Jira issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get

        Args:
            issue_id (str): The ID or key of the issue to get changelogs for.
            start_at (int): The index of the first item to return.
            max_results (int): The maximum number of results to return.

        Returns:
            list[dict]: A list of dictionaries containing the changelog history for the issue.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """

        return self._request_jira(
            method="GET",
            context_path=f"issue/{issue_id}/changelog",
            params={
                "startAt": start_at,
                "maxResults": max_results,
            },
            response_type=list,
        )

    @validate_call
    def edit_issue(
        self,
        issue_id: str,
        fields: dict,
        notify_users: bool = True,
        return_issue: bool = False,
        expand: str | None = None,
        override_screen_security: bool = False,
        override_editable_flag: bool = False,
        history_metadata: Any | None = None,
        properties: list[Any] | None = None,
        transitions: Any | None = None,
        update: dict | None = None,
        additional_properties: Any | None = None,
    ) -> dict[str, Any]:
        """Edit a Jira issue.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put

        Args:
            issue_id (str): The ID or key of the issue to edit.
            fields (dict): A dictionary containing the fields to update. Each field should be specified with its ID or key and the new value.
            notify_users (bool, optional): Whether to send email notifications for the update. Defaults to True.
            return_issue (bool, optional): Whether to return the updated issue. Defaults to False.
            expand (str, optional): A comma-separated list of properties to expand.
            override_screen_security (bool, optional): Whether to override screen security. Defaults to False.
            override_editable_flag (bool, optional): Whether to override the editable flag. Defaults to False.
            history_metadata (Any, optional): The history metadata.
            properties (list[Any], optional): The properties.
            transitions (Any, optional): The transitions.
            update (dict, optional): The update.
            additional_properties (Any, optional): The additional properties.

        Returns:
            dict: The updated issue details.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        return self._request_jira(
            method="PUT",
            context_path=f"issue/{issue_id}",
            params={
                "notifyUsers": notify_users,
                "overrideScreenSecurity": override_screen_security,
                "overrideEditableFlag": override_editable_flag,
                "returnIssue": return_issue,
                "expand": expand,
            },
            data={
                "fields": fields,
                "historyMetadata": history_metadata,
                "properties": properties,
                "transitions": transitions,
                "update": update,
                "additionalProperties": additional_properties,
            },
            response_type=dict,
        )
