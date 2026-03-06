"""Issue Search API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import ApiBase


class IssueSearch(ApiBase):
    """Issue Search API — search issues using JQL."""

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
        """Search for issues using JQL.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql: JQL query string (e.g., "project = PROJ AND status = 'In Progress'").
            next_page_token: Token for fetching the next page of results.
            max_results: Maximum items per page.
            fields: Fields to return (e.g., ["summary", "status"]). Use ["*all"] for all.
            expand: Comma-separated properties to expand.
            extra_params: Additional query parameters.
            extra_data: Additional request body data.

        Returns:
            Search results with issues, total, and nextPageToken.
        """
        return self._as_dict(
            self._client._request_jira(
                method="POST",
                context_path="search/jql",
                data={
                    "jql": jql,
                    "nextPageToken": next_page_token,
                    "maxResults": max_results,
                    "fields": fields,
                    "expand": expand,
                },
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )
