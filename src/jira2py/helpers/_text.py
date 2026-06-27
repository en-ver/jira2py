"""Internal text formatters for jira2py helper results."""

from __future__ import annotations

import json
from typing import Any

from ._adf import adf_to_markdown, is_adf_value
from ._utils import format_date, format_size
from .models import (
    AttachmentMeta,
    FieldMeta,
    IssueLink,
    IssueTransition,
    IssueType,
    JiraComment,
    JiraFilter,
    JiraIssue,
    JiraPriority,
    JiraProject,
    JiraStatus,
    JiraUser,
    JiraWorklog,
    SearchResult,
    WorklogReport,
    WorklogReportRow,
    user_display,
)

DEFAULT_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "labels",
    "components",
    "fixVersions",
    "description",
    "comment",
    "attachment",
    "subtasks",
    "issuelinks",
]

_FORMATTED_FIELDS = set(DEFAULT_FIELDS)


def _section(title: str) -> str:
    return f"--- [{title.upper()}] ---"


def _field_label(field_id: str, names_map: dict[str, str]) -> str:
    display = names_map.get(field_id)
    if display and display != field_id:
        return f"{display} ({field_id})"
    return field_id


def format_issue_full(
    issue: JiraIssue,
    *,
    url: str = "",
    requested_fields: list[str] | None = None,
    field_names: dict[str, str] | None = None,
) -> str:
    """Format a Jira issue for readable helper output."""
    fields = issue.fields
    lines: list[str] = [
        f"Key: {issue.key}",
        f"Summary: {fields.summary}",
        f"Status: {_named(fields.status)}",
        f"Type: {_named(fields.issuetype)}",
        f"Priority: {_named(fields.priority)}",
        f"Assignee: {user_display(fields.assignee)}",
        f"Reporter: {user_display(fields.reporter)}",
        f"Created: {format_date(fields.created)}",
        f"Updated: {format_date(fields.updated)}",
    ]

    if fields.labels:
        lines.append(f"Labels: {', '.join(fields.labels)}")

    if fields.components:
        lines.append(
            f"Components: {', '.join(component.name for component in fields.components)}"
        )

    if fields.fixVersions:
        lines.append(
            f"Fix Versions: {', '.join(version.name for version in fields.fixVersions)}"
        )

    if url:
        lines.append(f"URL: {url}")

    comment_page = fields.comment
    comment_total = comment_page.total if comment_page else 0
    lines.append(f"Comments: {comment_total}" if comment_total else "Comments: none")

    if fields.attachment:
        lines.append("")
        lines.append(_section(f"Attachments ({len(fields.attachment)})"))
        for attachment in fields.attachment:
            lines.append(
                f"- {attachment.filename or '?'} (id: {attachment.id}, {attachment.mimeType}, {format_size(attachment.size)})"
            )

    if fields.subtasks:
        lines.append("")
        lines.append(_section(f"Subtasks ({len(fields.subtasks)})"))
        for subtask in fields.subtasks:
            status = _named(subtask.fields.status)
            lines.append(f"- {subtask.key}: {subtask.fields.summary} [{status}]")

    if fields.issuelinks:
        lines.append("")
        lines.append(_section(f"Issue Links ({len(fields.issuelinks)})"))
        for link in fields.issuelinks:
            lines.append(_format_issue_link_line(link))

    lines.append("")
    lines.append(_section("Description"))
    lines.append(adf_to_markdown(fields.description))

    if requested_fields:
        extra_names = [
            name for name in requested_fields if name not in _FORMATTED_FIELDS
        ]
        if extra_names:
            extra_data: dict[str, Any] = {}
            raw_fields = issue.fields.model_extra or {}
            for name in extra_names:
                if name in raw_fields:
                    extra_data[name] = raw_fields[name]
                elif hasattr(issue.fields, name):
                    value = getattr(issue.fields, name)
                    if value is not None:
                        extra_data[name] = value
            if extra_data:
                names_map = field_names or {}
                lines.append("")
                lines.append(_section("Additional Fields"))
                adf_extra: dict[str, Any] = {}
                plain_fields: dict[str, Any] = {}
                for key, value in extra_data.items():
                    if is_adf_value(value):
                        adf_extra[key] = value
                    else:
                        plain_fields[key] = value
                for key, value in adf_extra.items():
                    label = _field_label(key, names_map)
                    lines.append(_section(label))
                    lines.append(adf_to_markdown(value))
                    lines.append("")
                if plain_fields:
                    labeled = {
                        _field_label(key, names_map): value
                        for key, value in plain_fields.items()
                    }
                    lines.append("```json")
                    lines.append(json.dumps(labeled, indent=2, default=str))
                    lines.append("```")

    return "\n".join(lines)


def format_comment(comment: JiraComment) -> str:
    """Format a single Jira comment."""
    author = user_display(comment.author)
    created = format_date(comment.created)
    updated = format_date(comment.updated)
    body = adf_to_markdown(comment.body)

    date_str = created
    if updated != created:
        date_str += f" (edited {updated})"

    return f"### {author} — {date_str}\n{body}"


def format_attachment_list(issue_key: str, attachments: list[AttachmentMeta]) -> str:
    """Format an explicit issue attachment list."""
    if not attachments:
        return f"No attachments on {issue_key}"

    lines = [f"Attachments on {issue_key}: {len(attachments)} total\n"]
    for attachment in attachments:
        lines.append(
            f"- {attachment.filename or '?'} "
            f"(id: {attachment.id}, {attachment.mimeType}, {format_size(attachment.size)})"
        )
    return "\n".join(lines)


def format_attachment_metadata(attachment: AttachmentMeta) -> str:
    """Format attachment metadata for display."""
    lines = [
        f"Attachment {attachment.id}: {attachment.filename or '?'}",
        f"Type: {attachment.mimeType}",
        f"Size: {format_size(attachment.size)}",
    ]
    if attachment.created:
        lines.append(f"Created: {format_date(attachment.created)}")
    if attachment.author:
        lines.append(f"Author: {user_display(attachment.author)}")
    if attachment.content:
        lines.append(f"Content URL: {attachment.content}")
    if attachment.thumbnail:
        lines.append(f"Thumbnail URL: {attachment.thumbnail}")
    return "\n".join(lines)


def format_issue_link_list(issue_key: str, links: list[IssueLink]) -> str:
    """Format an explicit issue-link list."""
    if not links:
        return f"No issue links on {issue_key}"

    lines = [f"Issue links on {issue_key}: {len(links)} total\n"]
    for link in links:
        lines.append(_format_issue_link_line(link))
    return "\n".join(lines)


def format_search_results(result: SearchResult, jql: str = "") -> str:
    """Format search results as a compact list."""
    if not result.issues:
        return f"No issues found for JQL: {jql}" if jql else "No issues found."

    lines = []
    for issue in result.issues:
        fields = issue.fields
        status = _named(fields.status)
        lines.append(
            f"{issue.key} — {fields.summary} [{status}] ({user_display(fields.assignee)})"
        )

    output = f"Found {len(result.issues)} issue(s)\n\n" + "\n".join(lines)
    if result.nextPageToken:
        output += "\n\n(more results available — refine JQL or increase max_results)"
    return output


def format_worklog(worklog: JiraWorklog) -> str:
    """Format a single Jira worklog."""
    author = worklog.author
    author_label = user_display(author)
    account_id = author.accountId if author else "?"

    lines = [f"Worklog {worklog.id or '?'} — {author_label} ({account_id})"]

    if worklog.issueId:
        lines.append(f"Issue ID: {worklog.issueId}")

    time_parts: list[str] = []
    if worklog.timeSpent:
        time_parts.append(worklog.timeSpent)
    if worklog.timeSpentSeconds:
        time_parts.append(f"{worklog.timeSpentSeconds}s")
    if time_parts:
        lines.append(f"Time spent: {' / '.join(time_parts)}")

    if worklog.started:
        lines.append(f"Started: {worklog.started}")
    if worklog.created:
        lines.append(f"Created: {format_date(worklog.created)}")
    if worklog.updated:
        lines.append(f"Updated: {format_date(worklog.updated)}")
    if worklog.updateAuthor:
        lines.append(f"Updated by: {_format_user(worklog.updateAuthor)}")
    if worklog.visibility:
        visibility_parts = [worklog.visibility.type or "?"]
        if worklog.visibility.value:
            visibility_parts.append(worklog.visibility.value)
        lines.append(f"Visibility: {' / '.join(visibility_parts)}")
    if worklog.comment:
        lines.append("Comment:")
        lines.extend(f"  {line}" for line in _format_worklog_comment(worklog.comment))

    return "\n".join(lines)


def format_worklog_list(
    issue_key: str,
    worklogs: list[JiraWorklog],
    *,
    start_at: int = 0,
    total: int | None = None,
    next_start: int | None = None,
) -> str:
    """Format an explicit issue worklog list."""
    if not worklogs:
        if start_at > 0 and total is not None:
            return f"No worklogs at offset {start_at} (total: {total})"
        return f"No worklogs on {issue_key}"

    if total is not None and (total > len(worklogs) or start_at > 0):
        end = start_at + len(worklogs)
        header = f"Worklogs on {issue_key}: showing {start_at + 1}–{end} of {total}"
    else:
        header = f"Worklogs on {issue_key}: {total or len(worklogs)} total"

    lines = [header, ""]
    for worklog in worklogs:
        lines.append(format_worklog(worklog))
        lines.append("")

    if next_start is not None and total is not None and next_start < total:
        lines.append(
            "--- More worklogs available. "
            f"Use start_at={next_start} to fetch the next page. ---"
        )

    return "\n".join(lines).rstrip()


def format_worklog_report(report: WorklogReport) -> str:
    """Format a worklog report as readable text."""
    selector = report.issueSelector
    account_label = report.accountId or "all users"
    lines = [
        "Worklog report",
        f"Date range: {report.startDate} to {report.endDate} (UTC; end date inclusive)",
        f"Account: {account_label}",
        f"JQL: {selector.jql}",
        (
            f"Issues scanned: {selector.issuesReturned} "
            f"(max {selector.maxIssues}{', truncated' if selector.truncated else ''})"
        ),
        f"Rows: {report.rowCount}",
        f"Total: {report.totalHours:.2f}h ({report.totalSeconds}s)",
    ]

    if selector.total is not None:
        lines.append(f"Issue search total: {selector.total}")
    if selector.nextPageToken:
        lines.append("More issues matched the JQL but were not scanned.")

    if not report.rows:
        lines.append("")
        lines.append("No matching worklogs found.")
        return "\n".join(lines)

    lines.append("")
    lines.append(_section(f"Rows ({report.rowCount})"))
    for row in report.rows:
        lines.extend(_format_worklog_row(row))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_issue_type_list(project_key: str, issue_types: list[IssueType]) -> str:
    """Format a list of issue types for display."""
    if not issue_types:
        return f"No issue types found for project {project_key}"
    lines = [f"Issue types for {project_key}:\n"]
    for issue_type in issue_types:
        subtask = " (subtask)" if issue_type.subtask else ""
        lines.append(f"  • {issue_type.name} (id: {issue_type.id}){subtask}")
    return "\n".join(lines)


def format_transition_list(
    issue_key: str,
    transitions: list[IssueTransition],
) -> str:
    """Format available issue transitions for display."""
    if not transitions:
        return f"No transitions available for {issue_key}"

    lines = [f"Available transitions for {issue_key}:\n"]
    for transition in transitions:
        target = f" → {transition.to.name}" if transition.to else ""
        required_fields = [
            field_id
            for field_id, meta in transition.fields.items()
            if isinstance(meta, dict) and meta.get("required")
        ]
        required_suffix = (
            f" [required fields: {', '.join(required_fields)}]"
            if required_fields
            else ""
        )
        lines.append(
            f"  • {transition.name} (id: {transition.id}){target}{required_suffix}"
        )
    return "\n".join(lines)


def format_field_metadata(
    project_key: str,
    type_name: str,
    fields: list[FieldMeta],
) -> str:
    """Format create/edit field metadata for display."""
    if not fields:
        return f"No fields found for {project_key} / {type_name}"

    required = [field for field in fields if field.required]
    optional = [field for field in fields if not field.required]
    lines = [f"Fields for {project_key} / {type_name}:\n"]

    if required:
        lines.append("Required:")
        for field in required:
            lines.extend(_format_field(field))

    if optional:
        lines.append("")
        lines.append("Optional:")
        for field in optional:
            lines.extend(_format_field(field))

    return "\n".join(lines)


def format_project(project: JiraProject) -> str:
    """Format a Jira project for display."""
    lines = [f"Project {project.key} — {project.name}"]
    if project.id:
        lines.append(f"ID: {project.id}")
    if project.projectTypeKey:
        lines.append(f"Type: {project.projectTypeKey}")
    if project.style:
        lines.append(f"Style: {project.style}")
    if project.lead:
        lines.append(f"Lead: {_format_user(project.lead)}")
    if project.description:
        lines.append("Description:")
        lines.append(project.description)
    return "\n".join(lines)


def format_status_list(statuses: list[JiraStatus]) -> str:
    """Format Jira statuses for display."""
    if not statuses:
        return "No statuses found"

    lines = [f"Jira statuses: {len(statuses)} total", ""]
    for status in statuses:
        category = (
            f" [category: {status.statusCategory.name}]"
            if status.statusCategory
            else ""
        )
        description = f" — {status.description}" if status.description else ""
        lines.append(f"- {status.name} (id: {status.id}){category}{description}")
    return "\n".join(lines)


def format_priority_list(priorities: list[JiraPriority]) -> str:
    """Format Jira priorities for display."""
    if not priorities:
        return "No priorities found"

    lines = [f"Jira priorities: {len(priorities)} total", ""]
    for priority in priorities:
        default_suffix = " [default]" if priority.isDefault else ""
        description = f" — {priority.description}" if priority.description else ""
        lines.append(
            f"- {priority.name} (id: {priority.id}){default_suffix}{description}"
        )
    return "\n".join(lines)


def format_filter_list(
    filters: list[JiraFilter],
    *,
    title: str,
    start_at: int = 0,
    total: int | None = None,
) -> str:
    """Format saved Jira filters for display."""
    if total is not None and (total > len(filters) or start_at > 0):
        end = start_at + len(filters)
        header = f"{title}: showing {start_at + 1}–{end} of {total}"
    else:
        header = f"{title}: {total or len(filters)} total"

    lines = [header, ""]
    for jira_filter in filters:
        owner = user_display(jira_filter.owner)
        lines.append(f"- {jira_filter.name} (id: {jira_filter.id}) — owner: {owner}")
        if jira_filter.jql:
            lines.append(f"  JQL: {jira_filter.jql}")
        if jira_filter.description:
            lines.append(f"  Description: {jira_filter.description}")
    return "\n".join(lines)


def _format_worklog_row(row: WorklogReportRow) -> list[str]:
    lines = [
        (
            f"- {row.dateTime} — {row.issueKey} — {row.displayName} "
            f"({row.accountId}) — {row.timeSpentHours:.2f}h"
        )
    ]

    detail_parts = [f"issueId: {row.issueId}"]
    if row.projectKey:
        detail_parts.append(f"project: {row.projectKey}")
    if row.issueSummary:
        detail_parts.append(f"summary: {row.issueSummary}")
    if row.worklogId:
        detail_parts.append(f"worklogId: {row.worklogId}")
    lines.append(f"  {' | '.join(detail_parts)}")

    time_parts: list[str] = []
    if row.timeSpent:
        time_parts.append(row.timeSpent)
    if row.timeSpentSeconds is not None:
        time_parts.append(f"{row.timeSpentSeconds}s")
    if time_parts:
        lines.append(f"  timeSpent: {' / '.join(time_parts)}")

    if row.started:
        lines.append(f"  started: {row.started}")
    if row.created:
        lines.append(f"  created: {row.created}")
    if row.updated:
        lines.append(f"  updated: {row.updated}")
    if row.updateAuthor:
        lines.append(f"  updateAuthor: {_format_user(row.updateAuthor)}")
    if row.visibility:
        visibility_parts = [row.visibility.type or "?"]
        if row.visibility.value:
            visibility_parts.append(row.visibility.value)
        lines.append(f"  visibility: {' / '.join(visibility_parts)}")
    if row.comment:
        lines.append("  comment:")
        lines.extend(f"    {line}" for line in _format_worklog_comment(row.comment))
    if row.properties:
        lines.append("  properties:")
        for line in json.dumps(row.properties, indent=2, default=str).splitlines():
            lines.append(f"    {line}")

    return lines


def _format_worklog_comment(comment: dict[str, Any]) -> list[str]:
    if is_adf_value(comment):
        return adf_to_markdown(comment).splitlines() or [""]
    return json.dumps(comment, indent=2, default=str).splitlines()


def _format_user(user: JiraUser) -> str:
    return f"{user.displayName} ({user.accountId})"


def _format_issue_link_line(link: IssueLink) -> str:
    if link.outwardIssue:
        target = link.outwardIssue
        direction = link.type.outward
    elif link.inwardIssue:
        target = link.inwardIssue
        direction = link.type.inward
    else:
        return f"- unresolved link (id: {link.id})"
    status = _named(target.fields.status)
    return (
        f"- {direction} {target.key}: {target.fields.summary} "
        f"[{status}] (link id: {link.id})"
    )


def _named(resource: Any) -> str:
    return resource.name if resource else "—"


def _format_field(field: FieldMeta) -> list[str]:
    lines: list[str] = []
    jira_schema = field.jira_schema
    schema_type = jira_schema.type if jira_schema else "unknown"
    custom = jira_schema.custom if jira_schema else ""
    custom_suffix = f" ({custom.split(':')[-1]})" if custom else ""
    lines.append(f'  {field.resolved_id} "{field.name}" — {schema_type}{custom_suffix}')

    if field.allowedValues:
        values = []
        for value in field.allowedValues[:30]:
            if isinstance(value, dict):
                values.append(value.get("name", value.get("value", json.dumps(value))))
            else:
                values.append(str(value))
        suffix = (
            f", ... ({len(field.allowedValues)} total)"
            if len(field.allowedValues) > 30
            else ""
        )
        lines.append(f"    Allowed values: {', '.join(values)}{suffix}")

    if field.defaultValue is not None:
        if isinstance(field.defaultValue, dict):
            default_value = field.defaultValue.get(
                "name",
                field.defaultValue.get("value", json.dumps(field.defaultValue)),
            )
        else:
            default_value = str(field.defaultValue)
        lines.append(f"    Default: {default_value}")

    return lines
