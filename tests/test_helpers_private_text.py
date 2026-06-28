from __future__ import annotations

from textwrap import dedent
from typing import cast

from jira2py.helpers._text import (
    format_attachment_list,
    format_attachment_metadata,
    format_filter_list,
    format_issue_full,
    format_issue_link_list,
    format_priority_list,
    format_project,
    format_search_results,
    format_status_list,
    format_transition_list,
    format_worklog,
    format_worklog_list,
)
from jira2py.helpers.models import (
    AttachmentMeta,
    IssueLink,
    IssueTransition,
    JiraFilter,
    JiraIssue,
    JiraPriority,
    JiraProject,
    JiraStatus,
    JiraWorklog,
    SearchResult,
)


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


def test_format_attachment_outputs_render_agent_readable_details() -> None:
    attachment = AttachmentMeta.model_validate(
        {
            "id": "10001",
            "filename": "debug.log",
            "mimeType": "text/plain",
            "size": 1536,
            "created": "2026-01-02T03:04:05.000+0000",
            "author": {"displayName": "Alice"},
            "content": "https://cdn.example.test/10001",
        }
    )

    assert format_attachment_list("PROJ-1", [attachment]) == (
        "Attachments on PROJ-1: 1 total\n\n- debug.log (id: 10001, text/plain, 1.5 KB)"
    )
    assert format_attachment_metadata(attachment) == (
        "Attachment 10001: debug.log\n"
        "Type: text/plain\n"
        "Size: 1.5 KB\n"
        "Created: 2026-01-02\n"
        "Author: Alice\n"
        "Content URL: https://cdn.example.test/10001"
    )


def test_format_issue_link_list_matches_issue_read_link_style() -> None:
    link = IssueLink.model_validate(
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
    )

    assert format_issue_link_list("PROJ-123", [link]) == (
        "Issue links on PROJ-123: 1 total\n\n"
        "- blocks PROJ-200: linked issue [Done] (link id: 55)"
    )


def test_format_transition_list_shows_targets_and_required_fields() -> None:
    transitions = [
        IssueTransition.model_validate(
            {
                "id": "11",
                "name": "Start Progress",
                "to": {"name": "In Progress"},
            }
        ),
        IssueTransition.model_validate(
            {
                "id": "21",
                "name": "Resolve Issue",
                "to": {"name": "Done"},
                "fields": {
                    "resolution": {"required": True},
                    "comment": {"required": False},
                },
            }
        ),
    ]

    assert (
        format_transition_list("PROJ-1", transitions)
        == dedent(
            """\
        Available transitions for PROJ-1:

          • Start Progress (id: 11) → In Progress
          • Resolve Issue (id: 21) → Done [required fields: resolution]
        """
        ).strip()
    )


def test_format_project_status_priority_and_filter_outputs() -> None:
    project = JiraProject.model_validate(
        {
            "id": "10000",
            "key": "PROJ",
            "name": "Project One",
            "projectTypeKey": "software",
            "style": "classic",
            "lead": {"displayName": "Alice", "accountId": "a1"},
            "description": "First project",
        }
    )
    statuses = [
        JiraStatus.model_validate(
            {
                "id": "1",
                "name": "To Do",
                "description": "Initial status",
                "statusCategory": {"id": 2, "key": "new", "name": "To Do"},
            }
        )
    ]
    priorities = [
        JiraPriority.model_validate(
            {
                "id": "5",
                "name": "Medium",
                "isDefault": True,
            }
        )
    ]
    filters = [
        JiraFilter.model_validate(
            {
                "id": "10100",
                "name": "My open issues",
                "owner": {"displayName": "Alice", "accountId": "acct-1"},
                "jql": "project = PROJ",
                "description": "Used daily",
            }
        )
    ]

    assert format_project(project) == (
        "Project PROJ — Project One\n"
        "ID: 10000\n"
        "Type: software\n"
        "Style: classic\n"
        "Lead: Alice (a1)\n"
        "Description:\n"
        "First project"
    )
    assert format_status_list(statuses) == (
        "Jira statuses: 1 total\n\n- To Do (id: 1) [category: To Do] — Initial status"
    )
    assert format_priority_list(priorities) == (
        "Jira priorities: 1 total\n\n- Medium (id: 5) [default]"
    )
    assert format_filter_list(filters, title="Saved filters", total=2) == (
        "Saved filters: showing 1–1 of 2\n\n"
        "- My open issues (id: 10100) — owner: Alice\n"
        "  JQL: project = PROJ\n"
        "  Description: Used daily"
    )


def test_format_worklog_output_renders_comment_and_paging_details() -> None:
    worklog = JiraWorklog.model_validate(
        {
            "id": "wl-1",
            "issueId": "10001",
            "author": {"displayName": "Alice", "accountId": "a1"},
            "updateAuthor": {"displayName": "Bob", "accountId": "b2"},
            "started": "2026-01-02T09:30:00+0200",
            "created": "2026-01-02T10:00:00.000+0000",
            "updated": "2026-01-03T11:00:00.000+0000",
            "timeSpent": "1h",
            "timeSpentSeconds": 3600,
            "visibility": {"type": "role", "value": "Developers"},
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
    )

    assert format_worklog(worklog) == (
        "Worklog wl-1 — Alice (a1)\n"
        "Issue ID: 10001\n"
        "Time spent: 1h / 3600s\n"
        "Started: 2026-01-02T09:30:00+0200\n"
        "Created: 2026-01-02\n"
        "Updated: 2026-01-03\n"
        "Updated by: Bob (b2)\n"
        "Visibility: role / Developers\n"
        "Comment:\n"
        "  Did work"
    )
    assert format_worklog_list(
        "PROJ-1",
        [worklog],
        start_at=1,
        total=3,
        next_start=2,
    ) == (
        "Worklogs on PROJ-1: showing 2–2 of 3\n\n"
        "Worklog wl-1 — Alice (a1)\n"
        "Issue ID: 10001\n"
        "Time spent: 1h / 3600s\n"
        "Started: 2026-01-02T09:30:00+0200\n"
        "Created: 2026-01-02\n"
        "Updated: 2026-01-03\n"
        "Updated by: Bob (b2)\n"
        "Visibility: role / Developers\n"
        "Comment:\n"
        "  Did work\n\n"
        "--- More worklogs available. Use start_at=2 to fetch the next page. ---"
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
