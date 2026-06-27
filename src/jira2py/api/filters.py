"""Filters API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class Filters(ApiBase):
    """Filters API — saved filter discovery and lookup."""

    def search_filters(
        self,
        *,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        filter_name: str | None = None,
        filter_ids: list[int] | None = None,
        account_id: str | None = None,
        order_by: str | None = None,
        expand: str | None = None,
        override_share_permissions: bool | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search saved Jira filters.

        Jira Cloud endpoint:
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-filters/#api-rest-api-3-filter-search-get
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path="filter/search",
                params={
                    "startAt": start_at,
                    "maxResults": max_results,
                    "filterName": filter_name,
                    "id": filter_ids,
                    "accountId": account_id,
                    "orderBy": order_by,
                    "expand": expand,
                    "overrideSharePermissions": override_share_permissions,
                },
                extra_params=extra_params,
            )
        )

    def get_filter(
        self,
        filter_id: str,
        *,
        expand: str | None = None,
        override_share_permissions: bool | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get a saved Jira filter by ID.

        Jira Cloud endpoint:
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-filters/#api-rest-api-3-filter-id-get
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"filter/{filter_id}",
                params={
                    "expand": expand,
                    "overrideSharePermissions": override_share_permissions,
                },
                extra_params=extra_params,
            )
        )
