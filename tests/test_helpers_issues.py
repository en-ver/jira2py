from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

import jira2py.helpers.issues as issues_module
from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.issues import IssueHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        issues=Mock(),
        fields=Mock(),
    )


def test_read_fetches_issue_with_default_and_extra_fields() -> None:
    api = _make_api()
    api.issues.get_issue.return_value = {
        "key": "PROJ-123",
        "names": {"customfield_10001": "Acceptance Criteria"},
        "fields": {
            "summary": "Fix thing",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Hello world"}],
                    }
                ],
            },
            "comment": {"total": 1},
            "customfield_10001": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Extra details"}],
                    }
                ],
            },
        },
    }

    result = IssueHelpers(cast(JiraAPI, api)).read(
        "PROJ-123",
        extra_fields=["customfield_10001", "summary"],
    )

    api.issues.get_issue.assert_called_once()
    assert api.issues.get_issue.call_args.kwargs == {
        "issue_id": "PROJ-123",
        "fields": (
            "summary,status,issuetype,priority,assignee,reporter,created,updated,"
            "labels,components,fixVersions,description,comment,attachment,subtasks,"
            "issuelinks,customfield_10001"
        ),
        "expand": "names",
    }
    assert result.data == api.issues.get_issue.return_value
    assert "Key: PROJ-123" in result.text
    assert "URL: https://example.atlassian.net/browse/PROJ-123" in result.text
    assert "Acceptance Criteria (customfield_10001)".upper() in result.text.upper()


def test_create_converts_description_and_markdown_fields(monkeypatch) -> None:
    api = _make_api()
    api.issues.create_issue.return_value = {"key": "PROJ-123"}
    helper = IssueHelpers(cast(JiraAPI, api))

    monkeypatch.setattr(
        issues_module,
        "convert_markdown_fields",
        lambda fields, adf_field_ids: {
            "customfield_10001": {"converted": fields["customfield_10001"]},
            "labels": fields["labels"],
        },
    )
    monkeypatch.setattr(
        helper,
        "_get_adf_field_ids",
        lambda: {"customfield_10001"},
    )
    monkeypatch.setattr(
        issues_module,
        "markdown_to_adf",
        lambda text: {"type": "doc", "markdown": text},
    )

    result = helper.create(
        "PROJ",
        "Bug",
        "Fix thing",
        description="Body",
        fields={"customfield_10001": "Extra details", "labels": ["backend"]},
    )

    api.issues.create_issue.assert_called_once_with(
        fields={
            "customfield_10001": {"converted": "Extra details"},
            "labels": ["backend"],
            "project": {"key": "PROJ"},
            "issuetype": {"name": "Bug"},
            "summary": "Fix thing",
            "description": {"type": "doc", "markdown": "Body"},
        }
    )
    assert result.text == (
        "Created PROJ-123: Fix thing\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )
    assert result.data == {"key": "PROJ-123"}


def test_create_raises_when_adf_field_metadata_lookup_fails() -> None:
    api = _make_api()
    api.fields.get_fields.side_effect = RuntimeError("metadata boom")
    helper = IssueHelpers(cast(JiraAPI, api))

    with pytest.raises(
        JiraHelperOperationError,
        match="Failed to fetch Jira field metadata needed for Markdown-to-ADF conversion",
    ) as exc_info:
        helper.create(
            "PROJ",
            "Bug",
            "Fix thing",
            fields={"customfield_10001": "Extra details"},
        )

    api.issues.create_issue.assert_not_called()
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == "metadata boom"


def test_edit_raw_response_handles_empty_response_body() -> None:
    api = _make_api()
    api.issues.edit_issue.return_value = None

    result = IssueHelpers(cast(JiraAPI, api)).edit(
        "PROJ-123", summary="Updated", raw=True
    )

    api.issues.edit_issue.assert_called_once_with(
        issue_id="PROJ-123",
        fields={"summary": "Updated"},
        return_issue=True,
    )
    assert result.data is None
    assert result.raw_content == "null"
    assert result.text == (
        "Successfully updated PROJ-123\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )


def test_validate_methods_reject_invalid_issue_input() -> None:
    helper = IssueHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="project_key"):
        helper.validate_create("   ", "Bug", "Summary")

    with pytest.raises(JiraHelperValidationError, match="Nothing to update"):
        helper.validate_edit("PROJ-123")

    with pytest.raises(JiraHelperValidationError, match="summary"):
        helper.validate_create(
            "PROJ",
            "Bug",
            "Summary",
            fields={"summary": "duplicate"},
        )


def test_read_wraps_underlying_jira_errors() -> None:
    api = _make_api()
    api.issues.get_issue.side_effect = RuntimeError("boom")

    with pytest.raises(
        JiraHelperOperationError, match="Failed to fetch issue PROJ-123"
    ):
        IssueHelpers(cast(JiraAPI, api)).read("PROJ-123")
