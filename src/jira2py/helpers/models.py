# ruff: noqa: N815
"""Foundational helper models for high-level jira2py helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JiraModel(BaseModel):
    """Base model that allows unknown Jira API fields to pass through."""

    model_config = ConfigDict(extra="allow")


class NamedResource(JiraModel):
    """A Jira resource with a name."""

    name: str = "—"


class JiraUser(JiraModel):
    """A Jira user."""

    displayName: str = "Unknown"
    accountId: str = "?"
    active: bool = True


class IssueRef(JiraModel):
    """Minimal issue reference."""

    key: str = "?"


class ProjectRef(JiraModel):
    """Minimal project reference embedded in issue fields."""

    key: str = "?"
    name: str = "?"


class AttachmentMeta(JiraModel):
    """Attachment metadata."""

    id: int = 0
    filename: str = ""
    mimeType: str = "application/octet-stream"
    size: int = 0


class JiraComment(JiraModel):
    """A single Jira comment."""

    author: JiraUser | None = None
    created: str | None = None
    updated: str | None = None
    body: dict[str, Any] | None = None


class CommentPage(JiraModel):
    """Paginated list of comments."""

    comments: list[JiraComment] = Field(default_factory=list)
    total: int = 0
    startAt: int = 0


class SubtaskFields(JiraModel):
    """Fields included in a subtask reference."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None


class Subtask(JiraModel):
    """A subtask reference within a parent issue."""

    key: str = "?"
    fields: SubtaskFields = Field(default_factory=SubtaskFields)


class IssueLinkType(JiraModel):
    """Type descriptor for an issue link."""

    name: str = "?"
    inward: str = "?"
    outward: str = "?"


class LinkedIssueFields(JiraModel):
    """Fields included in a linked issue reference."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None


class LinkedIssue(JiraModel):
    """A linked issue reference."""

    key: str = "?"
    fields: LinkedIssueFields = Field(default_factory=LinkedIssueFields)


class IssueLink(JiraModel):
    """A link between two issues."""

    id: str = ""
    type: IssueLinkType = Field(default_factory=IssueLinkType)
    inwardIssue: LinkedIssue | None = None
    outwardIssue: LinkedIssue | None = None


class IssueFields(JiraModel):
    """Fields of a Jira issue."""

    summary: str = "(no summary)"
    status: NamedResource | None = None
    issuetype: NamedResource | None = None
    priority: NamedResource | None = None
    assignee: JiraUser | None = None
    reporter: JiraUser | None = None
    project: ProjectRef | None = None
    created: str | None = None
    updated: str | None = None
    labels: list[str] = Field(default_factory=list)
    components: list[NamedResource] = Field(default_factory=list)
    fixVersions: list[NamedResource] = Field(default_factory=list)
    description: dict[str, Any] | None = None
    comment: CommentPage | None = None
    attachment: list[AttachmentMeta] = Field(default_factory=list)
    subtasks: list[Subtask] = Field(default_factory=list)
    issuelinks: list[IssueLink] = Field(default_factory=list)


class JiraIssue(JiraModel):
    """A Jira issue."""

    id: str = ""
    key: str = "?"
    fields: IssueFields = Field(default_factory=IssueFields)


class SearchResult(JiraModel):
    """Response from enhanced issue search."""

    issues: list[JiraIssue] = Field(default_factory=list)
    nextPageToken: str | None = None
    total: int | None = None
    isLast: bool | None = None


class JiraProject(JiraModel):
    """A Jira project."""

    key: str = "?"
    name: str = "?"


class ProjectSearchResult(JiraModel):
    """Response from project search."""

    values: list[JiraProject] = Field(default_factory=list)
    isLast: bool = True
    total: int | None = None


class WorklogVisibility(JiraModel):
    """Visibility restrictions applied to a worklog."""

    type: str | None = None
    value: str | None = None
    identifier: str | None = None


class JiraWorklog(JiraModel):
    """A Jira worklog entry."""

    id: str = ""
    issueId: str = ""
    author: JiraUser | None = None
    updateAuthor: JiraUser | None = None
    comment: dict[str, Any] | None = None
    visibility: WorklogVisibility | None = None
    created: str | None = None
    updated: str | None = None
    started: str | None = None
    timeSpent: str | None = None
    timeSpentSeconds: int = 0
    properties: list[Any] = Field(default_factory=list)


class WorklogPage(JiraModel):
    """Paginated worklog response for an issue."""

    worklogs: list[JiraWorklog] = Field(default_factory=list)
    startAt: int = 0
    maxResults: int = 0
    total: int = 0


class WorklogIssueSelector(JiraModel):
    """Metadata describing how issues were selected for a worklog report."""

    jql: str
    maxIssues: int
    issuesReturned: int
    truncated: bool = False
    nextPageToken: str | None = None
    total: int | None = None


class WorklogReportRow(JiraModel):
    """A normalized worklog report row."""

    dateTime: str
    issueId: str
    issueKey: str
    accountId: str
    displayName: str
    timeSpentHours: float
    worklogId: str | None = None
    issueSummary: str | None = None
    projectKey: str | None = None
    started: str | None = None
    created: str | None = None
    updated: str | None = None
    timeSpentSeconds: int | None = None
    timeSpent: str | None = None
    updateAuthor: JiraUser | None = None
    visibility: WorklogVisibility | None = None
    comment: dict[str, Any] | None = None
    properties: list[Any] | None = None


class WorklogReport(JiraModel):
    """Structured worklog report with rows plus metadata."""

    startDate: str
    endDate: str
    timezone: str = "UTC"
    endDateInclusive: bool = True
    startedAtOrAfter: str
    startedBefore: str
    accountId: str | None = None
    issueSelector: WorklogIssueSelector
    rowCount: int = 0
    totalSeconds: int = 0
    totalHours: float = 0.0
    rows: list[WorklogReportRow] = Field(default_factory=list)


class IssueType(JiraModel):
    """A Jira issue type."""

    id: str = "?"
    name: str = "?"
    subtask: bool = False


class FieldSchema(JiraModel):
    """Schema info for a field."""

    type: str = "unknown"
    custom: str = ""


class FieldMeta(JiraModel):
    """Metadata for a single field on a create or edit screen."""

    model_config = ConfigDict(
        extra="allow", validate_by_name=True, validate_by_alias=True
    )

    fieldId: str = ""
    key: str = ""
    id: str = ""
    name: str = "?"
    required: bool = False
    jira_schema: FieldSchema | None = Field(default=None, validation_alias="schema")
    allowedValues: list[Any] = Field(default_factory=list)
    defaultValue: Any = None

    @property
    def resolved_id(self) -> str:
        """Best available field identifier."""
        return self.fieldId or self.key or self.id or "?"


@dataclass(slots=True, frozen=True)
class AttachmentDownloadPlan:
    """Attachment metadata plus the planned output destination."""

    attachment_id: str
    filename: str
    output_file: str
    resolved_output: Path
    meta: AttachmentMeta
    content_url: str


def user_display(user: JiraUser | None) -> str:
    """Display a user name or a friendly unassigned fallback."""
    return user.displayName if user else "Unassigned"


__all__ = [
    "AttachmentDownloadPlan",
    "AttachmentMeta",
    "CommentPage",
    "FieldMeta",
    "FieldSchema",
    "IssueFields",
    "IssueLink",
    "IssueLinkType",
    "IssueRef",
    "IssueType",
    "JiraComment",
    "JiraIssue",
    "JiraModel",
    "JiraProject",
    "JiraUser",
    "JiraWorklog",
    "LinkedIssue",
    "LinkedIssueFields",
    "NamedResource",
    "ProjectRef",
    "ProjectSearchResult",
    "SearchResult",
    "Subtask",
    "SubtaskFields",
    "WorklogIssueSelector",
    "WorklogPage",
    "WorklogReport",
    "WorklogReportRow",
    "WorklogVisibility",
]
