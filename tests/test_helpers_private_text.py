from __future__ import annotations

from textwrap import dedent
from typing import cast

from jira2py.helpers._text import format_issue_full, format_search_results
from jira2py.helpers.models import JiraIssue, SearchResult


def _sample_issue_data() -> dict[str, object]:
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


def test_format_issue_full_renders_current_helper_markdown_output() -> None:
    sample_issue_data = _sample_issue_data()
    issue = JiraIssue.model_validate(sample_issue_data)

    formatted = format_issue_full(
        issue,
        url="https://example.atlassian.net/browse/PROJ-123",
        requested_fields=["summary", "customfield_10001", "customfield_10002"],
        field_names=cast(dict[str, str], sample_issue_data["names"]),
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


def test_format_search_results_includes_paging_hint() -> None:
    result = SearchResult.model_validate(
        {
            "issues": [
                {
                    "key": "PROJ-1",
                    "fields": {
                        "summary": "One",
                        "status": {"name": "Open"},
                        "assignee": {"displayName": "Alice"},
                    },
                },
                {
                    "key": "PROJ-2",
                    "fields": {
                        "summary": "Two",
                        "status": {"name": "Done"},
                        "assignee": None,
                    },
                },
            ],
            "nextPageToken": "tok",
        }
    )

    assert (
        format_search_results(result, jql="project = PROJ")
        == dedent(
            """\
        Found 2 issue(s)

        PROJ-1 — One [Open] (Alice)
        PROJ-2 — Two [Done] (Unassigned)

        (more results available — refine JQL or increase max_results)
        """
        ).strip()
    )
