"""Issue Search API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class IssueSearch(ApiBase):
    """Issue Search API — search issues using JQL."""

    def enhanced_search(
        self,
        jql: str,
        next_page_token: str | None = None,
        max_results: int = _DEFAULT_PAGE_SIZE,
        fields: list[str] | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
        extra_data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for issues using JQL.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql: JQL query string (e.g., "project = PROJ AND status = 'In Progress'").
            next_page_token: Token for fetching the next page of results. Omitted from
                the request body when ``None``.
            max_results: Maximum items per page.
            fields: Fields to return (e.g., ["summary", "status"]). Use ["*all"] for all.
                Omitted from the request body when ``None``.
            expand: Comma-separated properties to expand. Omitted from the request body
                when ``None``.
            extra_params: Additional query parameters. Takes priority over named parameters.
            extra_data: Additional request body data. Takes priority over named data parameters.

        Returns:
            Search results with issues, total, and nextPageToken.
        """
        body: dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
        }
        if next_page_token is not None:
            body["nextPageToken"] = next_page_token
        if fields is not None:
            body["fields"] = fields
        if expand is not None:
            body["expand"] = expand

        return self._as_dict(
            self._client._request_jira(
                method="POST",
                context_path="search/jql",
                data=body,
                extra_params=extra_params,
                extra_data=extra_data,
            )
        )
