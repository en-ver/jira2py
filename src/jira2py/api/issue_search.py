"""Unified IssueSearch API implementation using generic pattern."""

from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class IssueSearchBase(ApiBase[T]):
    """Base class for IssueSearch API - contains shared business logic."""

    def _enhanced_search_request_config(
        self,
        jql: str,
        next_page_token: str | None,
        max_results: int,
        fields: list[str] | None,
        expand: str | None,
        extra_params: Mapping[str, Any] | None,
        extra_data: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for enhanced_search.

        Args:
            jql: The JQL query string to search for issues.
            next_page_token: A token to fetch the next page of results.
            max_results: The maximum number of items to return per page.
            fields: A list of fields to return for each issue.
            expand: A comma-separated list of properties to expand.
            extra_params: Additional query parameters to include in the request.
            extra_data: Additional data parameters to include in the request body.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "POST",
            "context_path": "search/jql",
            "data": {
                "jql": jql,
                "nextPageToken": next_page_token,
                "maxResults": max_results,
                "fields": fields,
                "expand": expand,
            },
            "extra_params": extra_params,
            "extra_data": extra_data,
        }


class IssueSearch(IssueSearchBase[JiraClientSync]):
    """Synchronous IssueSearch API implementation."""

    @validate_call
    def enhanced_search(
        self,
        jql: str,
        next_page_token: str | None = None,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Searches for issues using JQL.

        Executes a JQL (Jira Query Language) search to find issues matching
        the specified criteria. Supports pagination via page tokens for efficient
        retrieval of large result sets.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql: The JQL query string to search for issues.
                Example: "project = PROJ AND status = 'In Progress'".
            next_page_token: A token to fetch the next page of results. Obtained from
                a previous search response's "nextPageToken" field. Defaults to None.
            max_results: The maximum number of items to return per page. Defaults to 50.
            fields: A list of fields to return for each issue. Use ["*all"] for all fields,
                or specify field names like ["summary", "status", "assignee"].
                Defaults to None (returns default fields).
            expand: A comma-separated list of properties to expand for each issue.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the search results including:
            - "startAt": The index of the first issue returned
            - "maxResults": The maximum number of results requested
            - "total": The total number of issues matching the query
            - "issues": List of issue dictionaries
            - "nextPageToken": Token for fetching the next page (if more results exist)

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If the JQL query is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.search.enhanced_search("project = PROJ AND status = 'Open'", max_results=10)
            >>> len(result["issues"])
            10
            >>> total = result["total"]
            >>> total
            45
        """
        request_config = self._enhanced_search_request_config(
            jql, next_page_token, max_results, fields, expand, extra_params, extra_data
        )
        return self._as_dict(self._client._request_jira(**request_config))


class IssueSearchAsync(IssueSearchBase[JiraClientAsync]):
    """Asynchronous IssueSearch API implementation."""

    @validate_call
    async def enhanced_search(
        self,
        jql: str,
        next_page_token: str | None = None,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Searches for issues using JQL (async version).

        Executes a JQL (Jira Query Language) search to find issues matching
        the specified criteria. Supports pagination via page tokens for efficient
        retrieval of large result sets.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql: The JQL query string to search for issues.
                Example: "project = PROJ AND status = 'In Progress'".
            next_page_token: A token to fetch the next page of results. Obtained from
                a previous search response's "nextPageToken" field. Defaults to None.
            max_results: The maximum number of items to return per page. Defaults to 50.
            fields: A list of fields to return for each issue. Use ["*all"] for all fields,
                or specify field names like ["summary", "status", "assignee"].
                Defaults to None (returns default fields).
            expand: A comma-separated list of properties to expand for each issue.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.
            extra_data: Additional data parameters to include in the request body.
                Defaults to None.

        Returns:
            A dictionary containing the search results including:
            - "startAt": The index of the first issue returned
            - "maxResults": The maximum number of results requested
            - "total": The total number of issues matching the query
            - "issues": List of issue dictionaries
            - "nextPageToken": Token for fetching the next page (if more results exist)

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If the JQL query is invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = await api.search.enhanced_search("project = PROJ AND status = 'Open'", max_results=10)
            >>> len(result["issues"])
            10
            >>> total = result["total"]
            >>> total
            45
        """
        request_config = self._enhanced_search_request_config(
            jql, next_page_token, max_results, fields, expand, extra_params, extra_data
        )
        return self._as_dict(await self._client._request_jira(**request_config))
