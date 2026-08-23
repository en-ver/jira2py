"""Internal text formatters for jira2py helper results."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
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

_KNOWN_ISSUE_FIELDS = frozenset(
    {
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
    }
)


def _section(title: str) -> str:
    return f"--- [{title.upper()}] ---"


def _field_label(field_id: str, names_map: Mapping[Any, Any]) -> str:
    display = names_map.get(field_id)
    if isinstance(display, str) and display and display != field_id:
        return f"{display} ({field_id})"
    return field_id


def format_issue(data: Mapping[str, Any], *, browse_url: str | None = None) -> str:
    """Format an already-retrieved Jira issue without changing its raw data.

    Only raw field keys present in ``data["fields"]`` are rendered. Arbitrary ADF
    values are converted here for presentation; the supplied response is otherwise
    left untouched.
    """
    if not isinstance(data, Mapping):
        raise TypeError("data must be a mapping")

    key = data.get("key")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("data must contain a non-empty issue key")

    fields = data.get("fields")
    if not isinstance(fields, Mapping):
        raise ValueError("data must contain a mapping-valued fields entry")

    names = data.get("names")
    names_map: Mapping[Any, Any] = names if isinstance(names, Mapping) else {}
    lines = [f"Key: {key}"]

    if "summary" in fields:
        lines.append(f"Summary: {_raw_text(fields['summary'])}")
    if "status" in fields:
        lines.append(f"Status: {_raw_named(fields['status'])}")
    if "issuetype" in fields:
        lines.append(f"Type: {_raw_named(fields['issuetype'])}")
    if "priority" in fields:
        lines.append(f"Priority: {_raw_named(fields['priority'])}")
    if "assignee" in fields:
        lines.append(f"Assignee: {_raw_user(fields['assignee'])}")
    if "reporter" in fields:
        lines.append(f"Reporter: {_raw_user(fields['reporter'])}")
    if "created" in fields:
        lines.append(f"Created: {_raw_date(fields['created'])}")
    if "updated" in fields:
        lines.append(f"Updated: {_raw_date(fields['updated'])}")
    if "labels" in fields:
        lines.append(f"Labels: {_raw_text_collection(fields['labels'])}")
    if "components" in fields:
        lines.append(f"Components: {_raw_named_collection(fields['components'])}")
    if "fixVersions" in fields:
        lines.append(f"Fix Versions: {_raw_named_collection(fields['fixVersions'])}")

    if browse_url is not None:
        lines.append(f"URL: {browse_url}")

    if "comment" in fields:
        lines.append(f"Comments: {_raw_comment_total(fields['comment'])}")

    if "attachment" in fields:
        attachments = _raw_sequence(fields["attachment"])
        if not attachments:
            lines.append("Attachments: none")
        else:
            lines.append("")
            lines.append(_section(f"Attachments ({len(attachments)})"))
            lines.extend(_format_raw_attachment(item) for item in attachments)

    if "subtasks" in fields:
        subtasks = _raw_sequence(fields["subtasks"])
        if not subtasks:
            lines.append("Subtasks: none")
        else:
            lines.append("")
            lines.append(_section(f"Subtasks ({len(subtasks)})"))
            lines.extend(_format_raw_subtask(item) for item in subtasks)

    if "issuelinks" in fields:
        links = _raw_sequence(fields["issuelinks"])
        if not links:
            lines.append("Issue Links: none")
        else:
            lines.append("")
            lines.append(_section(f"Issue Links ({len(links)})"))
            lines.extend(_format_raw_issue_link_line(item) for item in links)

    if "description" in fields:
        lines.append("")
        lines.append(_section("Description"))
        lines.append(adf_to_markdown(fields["description"]))

    adf_fields: list[tuple[str, Any]] = []
    plain_fields: dict[str, Any] = {}
    for raw_field_id, value in fields.items():
        field_id = str(raw_field_id)
        if field_id in _KNOWN_ISSUE_FIELDS:
            continue
        if is_adf_value(value):
            adf_fields.append((field_id, value))
        else:
            plain_fields[_field_label(field_id, names_map)] = value

    if adf_fields or plain_fields:
        lines.append("")
        lines.append(_section("Additional Fields"))
        for field_id, value in adf_fields:
            lines.append(_section(_field_label(field_id, names_map)))
            lines.append(adf_to_markdown(value))
            lines.append("")
        if plain_fields:
            lines.append("```json")
            lines.append(json.dumps(plain_fields, indent=2, default=str))
            lines.append("```")

    return "\n".join(lines).rstrip()


def _raw_text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value or fallback
    return str(value)


def _raw_mapping(value: Any) -> Mapping[Any, Any]:
    return value if isinstance(value, Mapping) else {}


def _raw_named(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "—"
    return _raw_text(value.get("name"))


def _raw_user(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "Unassigned"
    return _raw_text(value.get("displayName"), fallback="Unassigned")


def _raw_date(value: Any) -> str:
    return format_date(value if isinstance(value, str) else None)


def _raw_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _raw_text_collection(value: Any) -> str:
    values = _raw_sequence(value)
    if not values:
        return "none"
    return ", ".join(_raw_text(item) for item in values)


def _raw_named_collection(value: Any) -> str:
    values = _raw_sequence(value)
    if not values:
        return "none"
    return ", ".join(_raw_named(item) for item in values)


def _raw_comment_total(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "none"
    total = value.get("total")
    return _raw_text(total, fallback="none") if total else "none"


def _format_raw_attachment(attachment: Any) -> str:
    data = _raw_mapping(attachment)
    size = data.get("size")
    return (
        f"- {_raw_text(data.get('filename'), fallback='?')} "
        f"(id: {_raw_text(data.get('id'), fallback='?')}, "
        f"{_raw_text(data.get('mimeType'), fallback='?')}, "
        f"{format_size(size if isinstance(size, (int, float)) else -1)})"
    )


def _format_raw_subtask(subtask: Any) -> str:
    data = _raw_mapping(subtask)
    fields = _raw_mapping(data.get("fields"))
    return (
        f"- {_raw_text(data.get('key'), fallback='?')}: "
        f"{_raw_text(fields.get('summary'))} [{_raw_named(fields.get('status'))}]"
    )


def _format_raw_issue_link_line(link: Any) -> str:
    data = _raw_mapping(link)
    link_id = _raw_text(data.get("id"), fallback="?")
    outward = data.get("outwardIssue")
    inward = data.get("inwardIssue")
    link_type = _raw_mapping(data.get("type"))
    if isinstance(outward, Mapping):
        target = outward
        direction = _raw_text(link_type.get("outward"), fallback="?")
    elif isinstance(inward, Mapping):
        target = inward
        direction = _raw_text(link_type.get("inward"), fallback="?")
    else:
        return f"- unresolved link (id: {link_id})"

    target_fields = _raw_mapping(target.get("fields"))
    return (
        f"- {direction} {_raw_text(target.get('key'), fallback='?')}: "
        f"{_raw_text(target_fields.get('summary'))} "
        f"[{_raw_named(target_fields.get('status'))}] (link id: {link_id})"
    )


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
        output = f"No issues found for JQL: {jql}" if jql else "No issues found."
    else:
        lines = []
        for issue in result.issues:
            fields = issue.fields
            status = _named(fields.status)
            lines.append(
                f"{issue.key} — {fields.summary} [{status}] ({user_display(fields.assignee)})"
            )

        output = f"Found {len(result.issues)} issue(s)\n\n" + "\n".join(lines)

    if result.nextPageToken:
        output += (
            "\n\n(more results available — use next_page_token to fetch the next page)"
        )
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
