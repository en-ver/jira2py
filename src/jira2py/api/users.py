"""Unified Users API implementation using generic pattern."""

from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class UsersBase(ApiBase[T]):
    """Base class for Users API - contains shared business logic."""

    def _search_users_request_config(
        self,
        query: str,
        start_at: int,
        max_results: int,
        extra_params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for search_users.

        Args:
            query: A query string to search for users by display name or email.
            start_at: The index of the first item to return (0-based).
            max_results: The maximum number of results to return.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "user/search",
            "params": {
                "query": query,
                "startAt": start_at,
                "maxResults": max_results,
            },
            "extra_params": extra_params,
        }


class Users(UsersBase[JiraClientSync]):
    """Synchronous Users API implementation."""

    @validate_call
    def search_users(
        self,
        query: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for Jira users by name or email.

        Returns a list of users matching the query string. The search matches
        against display name and email address.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/#api-rest-api-3-user-search-get

        Args:
            query: A query string to search for users by display name or email
                (e.g., "john" or "john@example.com").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of results to return (max 1000).
                Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A list of user dictionaries, each containing:
            - "accountId": The user's Atlassian account ID
            - "displayName": The user's display name
            - "emailAddress": The user's email (if visible)
            - "active": Whether the user account is active
            - "accountType": The type of account (e.g., "atlassian", "app")

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> users = api.users.search_users("john")
            >>> for user in users:
            ...     print(f"{user['displayName']} ({user['accountId']})")
        """
        request_config = self._search_users_request_config(
            query,
            start_at,
            max_results,
            extra_params,
        )
        return self._as_list(self._client._request_jira(**request_config))


class UsersAsync(UsersBase[JiraClientAsync]):
    """Asynchronous Users API implementation."""

    @validate_call
    async def search_users(
        self,
        query: str,
        start_at: int = 0,
        max_results: int = 50,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for Jira users by name or email (async version).

        Returns a list of users matching the query string. The search matches
        against display name and email address.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/#api-rest-api-3-user-search-get

        Args:
            query: A query string to search for users by display name or email
                (e.g., "john" or "john@example.com").
            start_at: The index of the first item to return (0-based). Defaults to 0.
            max_results: The maximum number of results to return (max 1000).
                Defaults to 50.
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A list of user dictionaries, each containing:
            - "accountId": The user's Atlassian account ID
            - "displayName": The user's display name
            - "emailAddress": The user's email (if visible)
            - "active": Whether the user account is active
            - "accountType": The type of account (e.g., "atlassian", "app")

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> users = await api.users.search_users("john")
            >>> for user in users:
            ...     print(f"{user['displayName']} ({user['accountId']})")
        """
        request_config = self._search_users_request_config(
            query,
            start_at,
            max_results,
            extra_params,
        )
        return self._as_list(await self._client._request_jira(**request_config))
