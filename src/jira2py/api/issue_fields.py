"""Issue Fields API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import _DEFAULT_PAGE_SIZE, ApiBase


class IssueFields(ApiBase):
    """Issue Fields API — list system and custom fields."""

    def get_fields(self) -> list[dict[str, Any]]:
        """Get all system and custom issue fields.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            List of field objects with id, name, custom, schema, etc.
        """
        return self._as_list(
            self._client._request_jira(
                method="GET",
                context_path="field",
            )
        )

    def search_fields(
        self,
        *,
        start_at: int = 0,
        max_results: int = _DEFAULT_PAGE_SIZE,
        query: str | None = None,
        field_ids: list[str] | None = None,
        field_types: list[str] | None = None,
        project_ids: list[int] | None = None,
        order_by: str | None = None,
        expand: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get one paginated field catalog page.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-search-get

        Args:
            start_at: Index of the first field to return (0-based).
            max_results: Maximum fields to return in this page.
            query: Case-insensitive partial match against a field name or description.
            field_ids: Canonical Jira field IDs to include.
            field_types: Field types to include (``"system"`` or ``"custom"``).
            project_ids: Numeric Jira project IDs used as project context filters.
            order_by: Jira field-search ordering expression.
            expand: Comma-separated field properties to expand.
            extra_params: Additional query parameters. Takes priority over named
                parameters.

        Returns:
            One raw Jira page with ``values`` and Jira pagination metadata.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path="field/search",
                params={
                    "startAt": start_at,
                    "maxResults": max_results,
                    "query": query,
                    "id": field_ids,
                    "type": field_types,
                    "projectIds": project_ids,
                    "orderBy": order_by,
                    "expand": expand,
                },
                extra_params=extra_params,
            )
        )
