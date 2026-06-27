"""Grouped filter helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Sequence

from jira2py.api import JiraAPI

from ._text import format_filter_list
from ._validation import require_non_empty_string
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import FilterSearchResult
from .results import HelperResult
from .search import SearchHelpers

_FILTER_LIST_MAX_RESULTS = 100


class FiltersHelpers:
    """High-level grouped helpers for Jira saved filters."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api
        self._search = SearchHelpers(api)

    def list(
        self,
        *,
        start_at: int = 0,
        max_results: int = 50,
    ) -> HelperResult:
        """List saved Jira filters visible to the current user."""
        return self._search_filters(
            filter_name=None,
            title="Saved filters",
            empty_text="No filters found",
            start_at=start_at,
            max_results=max_results,
        )

    def search(
        self,
        query: str,
        *,
        start_at: int = 0,
        max_results: int = 50,
    ) -> HelperResult:
        """Search saved Jira filters by name."""
        query = require_non_empty_string(query, field_name="query")
        return self._search_filters(
            filter_name=query,
            title=f'Saved filters matching "{query}"',
            empty_text=f'No filters found matching "{query}"',
            start_at=start_at,
            max_results=max_results,
        )

    def run(
        self,
        filter_id: str,
        *,
        max_results: int = 20,
        fields: Sequence[str] | None = None,
    ) -> HelperResult:
        """Resolve a saved filter's JQL and run the normal issue search flow."""
        filter_id = require_non_empty_string(filter_id, field_name="filter_id")

        try:
            filter_data = self.api.filters.get_filter(filter_id=filter_id, expand="jql")
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch filter {filter_id}: {exc}"
            ) from exc

        jql = filter_data.get("jql")
        if not isinstance(jql, str) or not jql.strip():
            raise JiraHelperValidationError(
                f"Filter {filter_id} does not contain a saved JQL query."
            )

        return self._search.issues(jql.strip(), max_results=max_results, fields=fields)

    def _search_filters(
        self,
        *,
        filter_name: str | None,
        title: str,
        empty_text: str,
        start_at: int,
        max_results: int,
    ) -> HelperResult:
        limit = min(max_results, _FILTER_LIST_MAX_RESULTS)

        try:
            data = self.api.filters.search_filters(
                start_at=start_at,
                max_results=limit,
                filter_name=filter_name,
                expand="owner,jql",
                order_by="name",
            )
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to fetch filters: {exc}") from exc

        result = FilterSearchResult.model_validate(data)
        if not result.values:
            return HelperResult.with_data(empty_text, data)

        text = format_filter_list(
            result.values,
            title=title,
            start_at=start_at,
            total=result.total,
        )
        if not result.isLast:
            if result.total is not None:
                remaining = max(result.total - (start_at + len(result.values)), 0)
                text += f"\n\n... and {remaining} more (refine your search or increase max_results)"
            else:
                text += "\n\n... more filters available (refine your search or increase max_results)"
        return HelperResult.with_data(text, data)


__all__ = ["FiltersHelpers"]
