"""Grouped search helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Sequence

from jira2py.api import JiraAPI

from ._text import format_search_results
from ._validation import require_non_empty_string
from .errors import JiraHelperOperationError
from .models import SearchResult
from .results import HelperResult

_SEARCH_FIELDS = [
    "summary",
    "status",
    "assignee",
    "priority",
    "issuetype",
    "created",
    "updated",
]


class SearchHelpers:
    """High-level grouped helpers for Jira search operations."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def issues(
        self,
        jql: str,
        *,
        max_results: int = 20,
        fields: Sequence[str] | None = None,
    ) -> HelperResult:
        """Search Jira issues using JQL."""
        jql = require_non_empty_string(jql, field_name="jql")
        limit = min(max_results, 50)
        request_fields = list(fields) if fields is not None else list(_SEARCH_FIELDS)

        try:
            data = self.api.search.enhanced_search(
                jql=jql,
                max_results=limit,
                fields=request_fields,
            )
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to search issues: {exc}") from exc

        result = SearchResult.model_validate(data)
        return HelperResult.with_data(format_search_results(result, jql=jql), data)


__all__ = ["SearchHelpers"]
