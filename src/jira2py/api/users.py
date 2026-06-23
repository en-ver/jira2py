"""Users API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class Users(ApiBase):
    """Users API — search Jira users."""

    def search_users(
        self,
        query: str,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for Jira users by name or email.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/#api-rest-api-3-user-search-get

        Args:
            query: Search string for display name or email.
            start_at: Index of the first item to return (0-based).
            max_results: Maximum results to return (max 1000).
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            List of user objects with accountId, displayName, emailAddress, active.
        """
        return self._as_list(
            self._client._request_jira(
                method="GET",
                context_path="user/search",
                params={
                    "query": query,
                    "startAt": start_at,
                    "maxResults": max_results,
                },
                extra_params=extra_params,
            )
        )
