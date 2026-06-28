from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest

import jira2py.helpers.worklogs as worklogs_module
from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.worklogs import WorklogHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        search=Mock(),
        worklogs=Mock(),
    )


def test_list_worklogs_formats_paging_and_next_page_hint() -> None:
    api = _make_api()
    api.worklogs.get_worklogs.return_value = {
        "startAt": 1,
        "total": 3,
        "worklogs": [
            {
                "id": "wl-1",
                "issueId": "10001",
                "author": {"displayName": "Alice", "accountId": "a1"},
                "started": "2026-01-02T09:30:00+0200",
                "created": "2026-01-02T10:00:00+0200",
                "updated": "2026-01-02T10:15:00+0200",
                "timeSpent": "1h",
                "timeSpentSeconds": 3600,
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
            }
        ],
    }

    result = WorklogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        start_at=1,
        max_results=6000,
    )

    api.worklogs.get_worklogs.assert_called_once_with(
        issue_id="PROJ-1",
        start_at=1,
        max_results=5000,
    )
    assert result.data == api.worklogs.get_worklogs.return_value
    assert "Worklogs on PROJ-1: showing 2–2 of 3" in result.text
    assert "Worklog wl-1 — Alice (a1)" in result.text
    assert "Time spent: 1h / 3600s" in result.text
    assert "Did work" in result.text
    assert "Use start_at=2 to fetch the next page" in result.text


def test_add_worklog_converts_markdown_comment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _make_api()
    api.worklogs.add_worklog.return_value = {
        "id": "wl-1",
        "issueId": "10001",
        "author": {"displayName": "Alice", "accountId": "a1"},
        "started": "2026-01-02T09:30:00+0200",
        "timeSpent": "1h",
        "timeSpentSeconds": 3600,
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
    }
    monkeypatch.setattr(
        worklogs_module,
        "markdown_to_adf",
        lambda text: {"type": "doc", "markdown": text},
    )

    result = WorklogHelpers(cast(JiraAPI, api)).add(
        "PROJ-1",
        "1h",
        started="2026-01-02T09:30:00+0200",
        comment="Did **work**",
    )

    api.worklogs.add_worklog.assert_called_once_with(
        issue_id="PROJ-1",
        time_spent="1h",
        started="2026-01-02T09:30:00+0200",
        comment={"type": "doc", "markdown": "Did **work**"},
    )
    assert result.data == api.worklogs.add_worklog.return_value
    assert "Added worklog to PROJ-1" in result.text
    assert "Worklog wl-1 — Alice (a1)" in result.text
    assert "Did work" in result.text


def test_update_worklog_requires_update_fields_and_formats_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _make_api()
    helper = WorklogHelpers(cast(JiraAPI, api))

    with pytest.raises(
        JiraHelperValidationError,
        match="At least one of time_spent, started, or comment",
    ):
        helper.update("PROJ-1", "wl-1")

    api.worklogs.update_worklog.return_value = {
        "id": "wl-1",
        "issueId": "10001",
        "author": {"displayName": "Alice", "accountId": "a1"},
        "started": "2026-01-02T10:00:00+0200",
        "timeSpent": "2h",
        "timeSpentSeconds": 7200,
    }
    monkeypatch.setattr(
        worklogs_module,
        "markdown_to_adf",
        lambda text: {"type": "doc", "markdown": text},
    )

    result = helper.update(
        "PROJ-1",
        "wl-1",
        time_spent="2h",
        started="2026-01-02T10:00:00+0200",
        comment="Updated note",
    )

    api.worklogs.update_worklog.assert_called_once_with(
        issue_id="PROJ-1",
        worklog_id="wl-1",
        time_spent="2h",
        started="2026-01-02T10:00:00+0200",
        comment={"type": "doc", "markdown": "Updated note"},
    )
    assert result.data == api.worklogs.update_worklog.return_value
    assert "Updated worklog wl-1 on PROJ-1" in result.text
    assert "Time spent: 2h / 7200s" in result.text


def test_delete_worklog_returns_explicit_ids_without_confirmation() -> None:
    api = _make_api()

    result = WorklogHelpers(cast(JiraAPI, api)).delete("PROJ-1", "wl-1")

    api.worklogs.delete_worklog.assert_called_once_with(
        issue_id="PROJ-1",
        worklog_id="wl-1",
    )
    assert result.data == {
        "status": "deleted",
        "issue_key": "PROJ-1",
        "worklog_id": "wl-1",
    }
    assert result.text == "Deleted worklog wl-1 from PROJ-1"


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
