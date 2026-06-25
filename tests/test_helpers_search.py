from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.search import SearchHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(search=Mock())


def test_search_issues_clamps_limit_and_formats_results() -> None:
    api = _make_api()
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
        "nextPageToken": "next-token",
    }

    result = SearchHelpers(cast(JiraAPI, api)).issues("project = PROJ", max_results=80)

    api.search.enhanced_search.assert_called_once_with(
        jql="project = PROJ",
        max_results=50,
        fields=[
            "summary",
            "status",
            "assignee",
            "priority",
            "issuetype",
            "created",
            "updated",
        ],
    )
    assert result.data == api.search.enhanced_search.return_value
    assert "Found 1 issue(s)" in result.text
    assert "PROJ-1 — One [Open] (Alice)" in result.text
    assert "more results available" in result.text


def test_search_issues_validates_and_wraps_failures() -> None:
    helper = SearchHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="jql"):
        helper.issues("   ")

    api = _make_api()
    api.search.enhanced_search.side_effect = RuntimeError("boom")

    with pytest.raises(JiraHelperOperationError, match="Failed to search issues"):
        SearchHelpers(cast(JiraAPI, api)).issues("project = PROJ")
