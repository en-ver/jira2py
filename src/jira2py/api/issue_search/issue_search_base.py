"""Base class for IssueSearch API - contains shared business logic."""

from typing import Any

from jira2py.client import JiraClientSync, JiraClientAsync


class IssueSearchBase:
    """Base class for IssueSearch API - contains shared business logic."""

    def __init__(self, client: JiraClientSync | JiraClientAsync) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client = client

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
