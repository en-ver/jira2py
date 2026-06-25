from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.worklogs import WorklogHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        search=Mock(),
        worklogs=Mock(),
    )


def test_report_builds_filtered_worklog_report_with_details() -> None:
    api = _make_api()
    api.search.enhanced_search.return_value = {
        "issues": [
            {
                "id": "10001",
                "key": "PROJ-1",
                "fields": {
                    "summary": "Track work",
                    "project": {"key": "PROJ"},
                },
            }
        ],
        "total": 2,
        "nextPageToken": "cursor-1",
    }
    api.worklogs.get_worklogs.return_value = {
        "startAt": 0,
        "total": 3,
        "worklogs": [
            {
                "id": "wl-1",
                "issueId": "10001",
                "author": {"displayName": "Alice", "accountId": "a1"},
                "updateAuthor": {"displayName": "Bob", "accountId": "b2"},
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Did work"}],
                        }
                    ],
                },
                "visibility": {"type": "role", "value": "Developers"},
                "started": "2026-01-02T09:30:00+0200",
                "created": "2026-01-02T10:00:00+0200",
                "updated": "2026-01-02T10:15:00+0200",
                "timeSpent": "1h",
                "timeSpentSeconds": 3600,
                "properties": [{"key": "source", "value": "manual"}],
            },
            {
                "id": "wl-2",
                "issueId": "10001",
                "author": {"displayName": "Carol", "accountId": "c3"},
                "started": "2026-01-02T11:00:00Z",
                "timeSpentSeconds": 1800,
            },
            {
                "id": "wl-3",
                "issueId": "10001",
                "author": {"displayName": "Alice", "accountId": "a1"},
                "started": "2026-01-04T11:00:00Z",
                "timeSpentSeconds": 1800,
            },
        ],
    }

    result = WorklogHelpers(cast(JiraAPI, api)).report(
        start_date="2026-01-02",
        end_date="2026-01-03",
        jql="project = PROJ",
        account_id="a1",
        max_issues=1,
        include_details=True,
    )

    api.search.enhanced_search.assert_called_once_with(
        jql="project = PROJ",
        next_page_token=None,
        max_results=1,
        fields=["summary", "project"],
    )
    api.worklogs.get_worklogs.assert_called_once()
    assert api.worklogs.get_worklogs.call_args.kwargs["issue_id"] == "10001"
    assert api.worklogs.get_worklogs.call_args.kwargs["start_at"] == 0
    assert api.worklogs.get_worklogs.call_args.kwargs["max_results"] == 5000
    assert api.worklogs.get_worklogs.call_args.kwargs["extra_params"] == {
        "startedAfter": 1767311999999,
        "startedBefore": 1767484800000,
    }

    assert result.data is not None
    result_data = cast(dict[str, Any], result.data)
    assert result_data["rowCount"] == 1
    assert result_data["totalSeconds"] == 3600
    assert result_data["totalHours"] == 1.0
    assert result_data["issueSelector"] == {
        "jql": "project = PROJ",
        "maxIssues": 1,
        "issuesReturned": 1,
        "truncated": True,
        "nextPageToken": "cursor-1",
        "total": 2,
    }
    assert result_data["rows"][0]["dateTime"] == "2026-01-02T07:30:00Z"
    assert result_data["rows"][0]["issueSummary"] == "Track work"
    assert result_data["rows"][0]["updateAuthor"] == {
        "displayName": "Bob",
        "accountId": "b2",
        "active": True,
    }
    assert result_data["rows"][0]["comment"]["type"] == "doc"
    assert "Worklog report" in result.text
    assert "Rows: 1" in result.text
    assert "More issues matched the JQL but were not scanned." in result.text
    assert "Did work" in result.text


def test_report_validates_input_before_calling_jira() -> None:
    helper = WorklogHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="jql"):
        helper.report(start_date="2026-01-02", end_date="2026-01-03", jql="   ")

    with pytest.raises(JiraHelperValidationError, match="max_issues"):
        helper.report(
            start_date="2026-01-02",
            end_date="2026-01-03",
            jql="project = PROJ",
            max_issues=0,
        )

    with pytest.raises(JiraHelperValidationError, match="start_date"):
        helper.report(
            start_date="2026/01/02",
            end_date="2026-01-03",
            jql="project = PROJ",
        )


def test_report_wraps_search_errors() -> None:
    api = _make_api()
    api.search.enhanced_search.side_effect = RuntimeError("boom")

    with pytest.raises(
        JiraHelperOperationError,
        match="Failed to search issues for worklog report",
    ):
        WorklogHelpers(cast(JiraAPI, api)).report(
            start_date="2026-01-02",
            end_date="2026-01-03",
            jql="project = PROJ",
        )
