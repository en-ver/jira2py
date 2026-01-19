"""Unified IssueSearch API implementation using generic pattern."""

from typing import Any, TypeVar, cast

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
        extra_params: dict[str, Any] | None,
        extra_data: dict[str, Any] | None,
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
            "response_type": "dict",
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
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.
        """
        request_config = self._enhanced_search_request_config(
            jql, next_page_token, max_results, fields, expand, extra_params, extra_data
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )


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
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.
        """
        request_config = self._enhanced_search_request_config(
            jql, next_page_token, max_results, fields, expand, extra_params, extra_data
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )
