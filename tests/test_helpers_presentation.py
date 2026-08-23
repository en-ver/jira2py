"""Tests for public issue presentation."""

from __future__ import annotations

import inspect
import logging
from copy import deepcopy
from textwrap import dedent
from typing import Any, cast

import pytest

from jira2py.helpers import format_issue


def _sample_issue_data() -> dict[str, Any]:
    return {
        "key": "PROJ-123",
        "names": {"customfield_10001": "Acceptance Criteria"},
        "fields": {
            "summary": "Fix thing",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Alice"},
            "reporter": {"displayName": "Bob"},
            "created": "2026-01-02T03:04:05.000+0000",
            "updated": "2026-01-03T03:04:05.000+0000",
            "labels": ["backend", "urgent"],
            "components": [{"name": "API"}],
            "fixVersions": [{"name": "1.2.3"}],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Hello "},
                            {
                                "type": "text",
                                "text": "world",
                                "marks": [{"type": "strong"}],
                            },
                        ],
                    }
                ],
            },
            "comment": {"total": 2},
            "attachment": [
                {
                    "id": 7,
                    "filename": "debug.log",
                    "mimeType": "text/plain",
                    "size": 1536,
                }
            ],
            "subtasks": [
                {
                    "key": "PROJ-124",
                    "fields": {
                        "summary": "subtask summary",
                        "status": {"name": "To Do"},
                    },
                }
            ],
            "issuelinks": [
                {
                    "id": "55",
                    "type": {"inward": "is blocked by", "outward": "blocks"},
                    "outwardIssue": {
                        "key": "PROJ-200",
                        "fields": {
                            "summary": "linked issue",
                            "status": {"name": "Done"},
                        },
                    },
                }
            ],
            "customfield_10001": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Extra field"}],
                    }
                ],
            },
            "customfield_10002": {"foo": "bar"},
        },
    }


def test_format_issue_renders_only_raw_field_keys() -> None:
    formatted = format_issue(
        {
            "key": "PROJ-123",
            "fields": {"summary": "Fix thing"},
        }
    )

    assert formatted == "Key: PROJ-123\nSummary: Fix thing"


def test_format_issue_renders_present_empty_values_truthfully() -> None:
    formatted = format_issue(
        {
            "key": "PROJ-123",
            "fields": {
                "summary": "",
                "status": None,
                "issuetype": {},
                "priority": {"name": ""},
                "assignee": None,
                "reporter": {},
                "created": None,
                "updated": "",
                "labels": [],
                "components": None,
                "fixVersions": [],
                "comment": {},
                "attachment": [],
                "subtasks": [],
                "issuelinks": [],
                "description": None,
            },
        }
    )

    assert (
        formatted
        == dedent(
            """\
        Key: PROJ-123
        Summary: —
        Status: —
        Type: —
        Priority: —
        Assignee: Unassigned
        Reporter: Unassigned
        Created: —
        Updated: —
        Labels: none
        Components: none
        Fix Versions: none
        Comments: none
        Attachments: none
        Subtasks: none
        Issue Links: none

        --- [DESCRIPTION] ---
        (none)
        """
        ).strip()
    )


def test_format_issue_uses_custom_field_names_only_when_supplied() -> None:
    data = {
        "key": "PROJ-123",
        "fields": {
            "customfield_10001": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Extra field"}],
                    }
                ],
            },
            "customfield_10002": {"foo": "bar"},
        },
    }

    without_names = format_issue(data)
    assert "--- [CUSTOMFIELD_10001] ---" in without_names
    assert '"customfield_10002"' in without_names

    with_names = format_issue(
        {
            **data,
            "names": {
                "customfield_10001": "Acceptance Criteria",
                "customfield_10002": "Risk",
            },
        }
    )
    assert "--- [ACCEPTANCE CRITERIA (CUSTOMFIELD_10001)] ---" in with_names
    assert '"Risk (customfield_10002)"' in with_names


def test_format_issue_is_pure_and_browse_url_is_optional() -> None:
    data = _sample_issue_data()
    original = deepcopy(data)

    formatted = format_issue(
        data,
        browse_url="https://example.atlassian.net/browse/PROJ-123",
    )

    assert data == original
    assert "Hello **world**" in formatted
    assert "URL: https://example.atlassian.net/browse/PROJ-123" in formatted
    assert "URL:" not in format_issue(data)


def test_format_issue_renders_current_helper_markdown_output() -> None:
    formatted = format_issue(
        _sample_issue_data(),
        browse_url="https://example.atlassian.net/browse/PROJ-123",
    )

    assert (
        formatted
        == dedent(
            """\
        Key: PROJ-123
        Summary: Fix thing
        Status: In Progress
        Type: Bug
        Priority: High
        Assignee: Alice
        Reporter: Bob
        Created: 2026-01-02
        Updated: 2026-01-03
        Labels: backend, urgent
        Components: API
        Fix Versions: 1.2.3
        URL: https://example.atlassian.net/browse/PROJ-123
        Comments: 2

        --- [ATTACHMENTS (1)] ---
        - debug.log (id: 7, text/plain, 1.5 KB)

        --- [SUBTASKS (1)] ---
        - PROJ-124: subtask summary [To Do]

        --- [ISSUE LINKS (1)] ---
        - blocks PROJ-200: linked issue [Done] (link id: 55)

        --- [DESCRIPTION] ---
        Hello **world**

        --- [ADDITIONAL FIELDS] ---
        --- [ACCEPTANCE CRITERIA (CUSTOMFIELD_10001)] ---
        Extra field

        ```json
        {
          "customfield_10002": {
            "foo": "bar"
          }
        }
        ```
        """
        ).strip()
    )


def test_format_issue_signature_requires_keyword_only_browse_url() -> None:
    signature = inspect.signature(format_issue)

    assert tuple(signature.parameters) == ("data", "browse_url")
    assert signature.parameters["browse_url"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        cast(Any, format_issue)(
            {"key": "PROJ-123", "fields": {}},
            "https://example.atlassian.net/browse/PROJ-123",
        )


@pytest.mark.parametrize("field_id", ["description", "customfield_10001"])
def test_format_issue_malformed_adf_uses_fallback_without_output(
    field_id: str,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    malformed_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "unsupported",
                "content": [{"type": "text", "text": "Fallback text"}],
            }
        ],
    }

    caplog.set_level(logging.DEBUG)
    formatted = format_issue({"key": "PROJ-123", "fields": {field_id: malformed_adf}})
    captured = capsys.readouterr()

    assert "Fallback text" in formatted
    assert captured.out == ""
    assert captured.err == ""
    assert not caplog.records


@pytest.mark.parametrize(
    ("data", "error"),
    [
        (None, TypeError),
        ({}, ValueError),
        ({"key": "", "fields": {}}, ValueError),
        ({"key": "PROJ-123", "fields": []}, ValueError),
    ],
)
def test_format_issue_requires_a_valid_issue_envelope(
    data: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        format_issue(cast(Any, data))
