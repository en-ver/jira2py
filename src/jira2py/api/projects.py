"""Projects API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class Projects(ApiBase):
    """Projects API — search, list, and get Jira projects."""

    def get_project(
        self,
        project_id_or_key: str,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get a single Jira project by explicit key or ID.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-projectidorkey-get

        Args:
            project_id_or_key: The Jira project key or numeric project ID.
            expand: Comma-separated properties to expand.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Jira project details for the requested project.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"project/{project_id_or_key}",
                params={"expand": expand},
                extra_params=extra_params,
            )
        )

    def search_projects(
        self,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        project_ids: list[int] | None = None,
        keys: list[str] | None = None,
        query: str | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for Jira projects.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get

        Args:
            start_at: Index of the first item to return (0-based).
            max_results: Maximum items per page (max 100).
            project_ids: Project IDs to filter by (up to 50).
            keys: Project keys to filter by (up to 50).
            query: Filter by matching key or name (case insensitive).
            expand: Comma-separated properties to expand
                (description, projectKeys, lead, issueTypes, url, insight).
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Paginated results with startAt, maxResults, total, isLast, and values.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path="project/search",
                params={
                    "startAt": start_at,
                    "maxResults": max_results,
                    "id": project_ids,
                    "keys": keys,
                    "query": query,
                    "expand": expand,
                },
                extra_params=extra_params,
            )
        )
