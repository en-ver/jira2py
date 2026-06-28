from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.filters import FiltersHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(filters=Mock(), search=Mock())


def test_list_formats_filter_results_and_more_hint() -> None:
    api = _make_api()
    api.filters.search_filters.return_value = {
        "values": [
            {
                "id": "10100",
                "name": "My open issues",
                "owner": {"displayName": "Alice Example", "accountId": "acct-1"},
                "jql": "assignee = currentUser() AND resolution = Unresolved",
            }
        ],
        "isLast": False,
        "total": 2,
    }

    result = FiltersHelpers(cast(JiraAPI, api)).list(max_results=150)

    api.filters.search_filters.assert_called_once_with(
        start_at=0,
        max_results=100,
        filter_name=None,
        expand="owner,jql",
        order_by="name",
    )
    assert result.data == api.filters.search_filters.return_value
    assert result.text == (
        "Saved filters: showing 1–1 of 2\n\n"
        "- My open issues (id: 10100) — owner: Alice Example\n"
        "  JQL: assignee = currentUser() AND resolution = Unresolved\n\n"
        "... and 1 more (refine your search or increase max_results)"
    )


def test_search_formats_matching_filters() -> None:
    api = _make_api()
    api.filters.search_filters.return_value = {
        "values": [
            {
                "id": "10101",
                "name": "Triage queue",
                "owner": {"displayName": "Bob Example", "accountId": "acct-2"},
                "jql": "project = TRIAGE",
                "description": "Used by support",
            }
        ],
        "isLast": True,
        "total": 1,
    }

    result = FiltersHelpers(cast(JiraAPI, api)).search("triage")

    api.filters.search_filters.assert_called_once_with(
        start_at=0,
        max_results=50,
        filter_name="triage",
        expand="owner,jql",
        order_by="name",
    )
    assert result.text == (
        'Saved filters matching "triage": 1 total\n\n'
        "- Triage queue (id: 10101) — owner: Bob Example\n"
        "  JQL: project = TRIAGE\n"
        "  Description: Used by support"
    )


def test_run_resolves_filter_jql_and_returns_normal_search_shape() -> None:
    api = _make_api()
    api.filters.get_filter.return_value = {
        "id": "10100",
        "name": "My open issues",
        "jql": "project = PROJ ORDER BY updated DESC",
    }
    api.search.enhanced_search.return_value = {
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "One",
                    "status": {"name": "Open"},
                    "assignee": {"displayName": "Alice"},
                },
            }
        ],
        "total": 1,
    }

    result = FiltersHelpers(cast(JiraAPI, api)).run(
        "10100",
        max_results=10,
        fields=["summary", "status", "assignee"],
    )

    api.filters.get_filter.assert_called_once_with(filter_id="10100", expand="jql")
    api.search.enhanced_search.assert_called_once_with(
        jql="project = PROJ ORDER BY updated DESC",
        max_results=10,
        fields=["summary", "status", "assignee"],
    )
    assert result.data == api.search.enhanced_search.return_value
    assert result.text == "Found 1 issue(s)\n\nPROJ-1 — One [Open] (Alice)"


def test_run_rejects_filters_without_saved_jql() -> None:
    api = _make_api()
    api.filters.get_filter.return_value = {"id": "10100", "name": "Broken filter"}

    with pytest.raises(
        JiraHelperValidationError,
        match="does not contain a saved JQL query",
    ):
        FiltersHelpers(cast(JiraAPI, api)).run("10100")

    api.search.enhanced_search.assert_not_called()


def test_search_and_run_wrap_failures() -> None:
    helper = FiltersHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="query"):
        helper.search("   ")

    api = _make_api()
    api.filters.search_filters.side_effect = RuntimeError("boom")
    with pytest.raises(JiraHelperOperationError, match="Failed to fetch filters"):
        FiltersHelpers(cast(JiraAPI, api)).list()

    api = _make_api()
    api.filters.get_filter.side_effect = RuntimeError("boom")
    with pytest.raises(JiraHelperOperationError, match="Failed to fetch filter 10100"):
        FiltersHelpers(cast(JiraAPI, api)).run("10100")
