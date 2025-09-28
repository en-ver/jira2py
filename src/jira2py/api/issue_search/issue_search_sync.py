"""Synchronous IssueSearch API implementation."""

from typing import Any, cast

from pydantic import validate_call

from jira2py.client import JiraClientSync, JiraCredentials

from .issue_search import IssueSearchBase


class IssueSearch(IssueSearchBase):
    """A class to interact with Jira's issue search API (synchronous)."""

    def __init__(self, credentials: JiraCredentials | None = None):
        """Initialize the IssueSearch client.

        Args:
            credentials: JIRA authentication credentials. If None, loads from environment.
        """
        super().__init__(JiraClientSync(credentials))

    @validate_call
    def enhanced_search(
        self,
        jql: str,
        next_page_token: str | None = None,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: str | None = None,
        extra_params: dict[str, Any] | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Searches for issues using JQL.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql (str): The JQL query string to search for issues.
            next_page_token (str, optional): A token to fetch the next page of results.
            max_results (int, optional): The maximum number of items to return per page. Defaults to 50.
            fields (list[str], optional): A list of fields to return for each issue. Use "*all" for all fields.
            expand (str, optional): A comma-separated list of properties to expand.
            extra_params (dict[str, Any] | None): Additional query parameters to include in the request.
            extra_data (dict[str, Any] | None): Additional data parameters to include in the request body.

        Returns:
            dict: A dictionary containing the search results, including issues and metadata.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        request_config = self._enhanced_search_request_config(
            jql, next_page_token, max_results, fields, expand, extra_params, extra_data
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )
