"""Unified Projects API implementation using generic pattern."""

from typing import Any, TypeVar, cast

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class ProjectsBase(ApiBase[T]):
    """Base class for Projects API - contains shared business logic."""

    def _search_projects_request_config(
        self,
        start_at: int,
        max_results: int,
        project_ids: list[int] | None,
        keys: list[str] | None,
        query: str | None,
        expand: list[str] | None,
        extra_params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for search_projects.

        Args:
            start_at: The index of the first item to return in a page of results (page offset).
            max_results: The maximum number of items to return per page. Max 100.
            project_ids: The project IDs to filter the results by. Up to 50 IDs can be provided.
            keys: The project keys to filter the results by. Up to 50 keys can be provided.
            query: Filter the results using a literal string. Projects with a matching key or name are returned (case insensitive).
            expand: A list of properties to expand. Options include: description, projectKeys, lead, issueTypes, url, insight.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "project/search",
            "params": {
                "startAt": start_at,
                "maxResults": max_results,
                "id": project_ids,
                "keys": keys,
                "query": query,
                "expand": _format_expand(expand) if expand else None,
            },
            "extra_params": extra_params,
            "response_type": "dict",
        }


def _format_expand(expand: list[str]) -> str:
    """Format expand list into comma-separated string.

    Args:
        expand: List of expand options.

    Returns:
        Comma-separated string of expand options.
    """
    return ",".join(expand)


class Projects(ProjectsBase[JiraClientSync]):
    """Synchronous Projects API implementation."""

    @validate_call
    def search_projects(
        self,
        start_at: int = 0,
        max_results: int = 50,
        project_ids: list[int] | None = None,
        keys: list[str] | None = None,
        query: str | None = None,
        expand: list[str] | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for Jira projects.

        Retrieves a paginated list of projects matching the specified criteria.
        Supports filtering by project IDs, keys, query string, and expanding properties.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get

        Args:
            start_at: The index of the first item to return in a page of results (page offset).
                Defaults to 0.
            max_results: The maximum number of items to return per page. Must be less than or equal to 100.
                Defaults to 50. Maximum: 100.
            project_ids: The project IDs to filter the results by. Up to 50 project IDs can be provided.
                Defaults to None (no filtering by ID).
            keys: The project keys to filter the results by. Up to 50 project keys can be provided.
                Defaults to None (no filtering by key).
            query: Filter the results using a literal string. Projects with a matching key or name
                are returned (case insensitive). Defaults to None (no filtering).
            expand: A list of properties to expand in the response. Options include:
                - "description": Returns the project description.
                - "projectKeys": Returns all project keys associated with a project.
                - "lead": Returns information about the project lead.
                - "issueTypes": Returns all issue types associated with the project.
                - "url": Returns the URL associated with the project.
                - "insight": EXPERIMENTAL. Returns the insight details of total issue count and last issue update time.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the search results with the following keys:
                - "startAt": The index of the first item returned.
                - "maxResults": The maximum number of results that could be returned.
                - "total": The total number of items matching the query.
                - "isLast": Whether this is the last page of results.
                - "values": A list of project dictionaries, each containing:
                    - "id": The unique ID of the project.
                    - "key": The project key (e.g., "PROJ").
                    - "name": The name of the project.
                    Additional properties as requested by expand parameter.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If query parameters are invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.projects.search_projects()
            >>> for project in result["values"]:
            ...     print(project["key"], project["name"])
            >>> result = api.projects.search_projects(query="Service", max_results=10)
            >>> result = api.projects.search_projects(keys=["PROJ", "TEST"], expand=["description", "lead"])
        """
        request_config = self._search_projects_request_config(
            start_at,
            max_results,
            project_ids,
            keys,
            query,
            expand,
            extra_params,
        )
        return cast(
            dict[str, Any],
            self._client._request_jira(**request_config),
        )


class ProjectsAsync(ProjectsBase[JiraClientAsync]):
    """Asynchronous Projects API implementation."""

    @validate_call
    async def search_projects(
        self,
        start_at: int = 0,
        max_results: int = 50,
        project_ids: list[int] | None = None,
        keys: list[str] | None = None,
        query: str | None = None,
        expand: list[str] | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for Jira projects (async version).

        Retrieves a paginated list of projects matching the specified criteria.
        Supports filtering by project IDs, keys, query string, and expanding properties.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get

        Args:
            start_at: The index of the first item to return in a page of results (page offset).
                Defaults to 0.
            max_results: The maximum number of items to return per page. Must be less than or equal to 100.
                Defaults to 50. Maximum: 100.
            project_ids: The project IDs to filter the results by. Up to 50 project IDs can be provided.
                Defaults to None (no filtering by ID).
            keys: The project keys to filter the results by. Up to 50 project keys can be provided.
                Defaults to None (no filtering by key).
            query: Filter the results using a literal string. Projects with a matching key or name
                are returned (case insensitive). Defaults to None (no filtering).
            expand: A list of properties to expand in the response. Options include:
                - "description": Returns the project description.
                - "projectKeys": Returns all project keys associated with a project.
                - "lead": Returns information about the project lead.
                - "issueTypes": Returns all issue types associated with the project.
                - "url": Returns the URL associated with the project.
                - "insight": EXPERIMENTAL. Returns the insight details of total issue count and last issue update time.
                Defaults to None.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing the search results with the following keys:
                - "startAt": The index of the first item returned.
                - "maxResults": The maximum number of results that could be returned.
                - "total": The total number of items matching the query.
                - "isLast": Whether this is the last page of results.
                - "values": A list of project dictionaries, each containing:
                    - "id": The unique ID of the project.
                    - "key": The project key (e.g., "PROJ").
                    - "name": The name of the project.
                    Additional properties as requested by expand parameter.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraValidationError: If query parameters are invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = await api.projects.search_projects()
            >>> for project in result["values"]:
            ...     print(project["key"], project["name"])
            >>> result = await api.projects.search_projects(query="Service", max_results=10)
            >>> result = await api.projects.search_projects(keys=["PROJ", "TEST"], expand=["description", "lead"])
        """
        request_config = self._search_projects_request_config(
            start_at,
            max_results,
            project_ids,
            keys,
            query,
            expand,
            extra_params,
        )
        return cast(
            dict[str, Any],
            await self._client._request_jira(**request_config),
        )
