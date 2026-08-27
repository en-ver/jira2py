from __future__ import annotations

from textwrap import dedent

from jira2py.helpers._text import (
    format_attachment_list,
    format_attachment_metadata,
    format_changelog_list,
    format_filter_list,
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
    JiraChangelog,
    JiraFilter,
    JiraPriority,
    JiraProject,
    JiraStatus,
    JiraWorklog,
    SearchResult,
)


def test_format_changelog_list_includes_each_history_and_item() -> None:
    changelog = JiraChangelog.model_validate(
        {
            "id": "10001",
            "created": "2026-01-02T03:04:05Z",
            "author": {"displayName": "Alice"},
            "items": [
                {"field": "status", "fromString": "Open", "toString": "Done"},
                {"fieldId": "customfield_10001", "from": "A", "to": "B"},
            ],
        }
    )

    assert format_changelog_list("PROJ-1", [changelog]) == (
        "Changelogs on PROJ-1: 1 returned\n\n"
        "- 2026-01-02T03:04:05Z — Alice — id 10001\n"
        "  - status: Open → Done\n"
        "  - customfield_10001: A → B"
    )
    assert format_changelog_list("PROJ-1", []) == "No changelogs returned for PROJ-1"


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

        (more results available — use next_page_token to fetch the next page)
        """
        ).strip()
    )


def test_format_search_results_includes_paging_hint_for_empty_page() -> None:
    result = SearchResult.model_validate({"issues": [], "nextPageToken": "tok"})

    assert format_search_results(result, jql="project = PROJ") == (
        "No issues found for JQL: project = PROJ\n\n"
        "(more results available — use next_page_token to fetch the next page)"
    )
