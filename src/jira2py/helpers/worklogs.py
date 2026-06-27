"""Grouped worklog helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from jira2py.api import JiraAPI

from ._adf import markdown_to_adf
from ._text import format_worklog, format_worklog_list, format_worklog_report
from ._validation import require_non_empty_string, validate_date_range
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import (
    JiraIssue,
    JiraWorklog,
    SearchResult,
    WorklogIssueSelector,
    WorklogPage,
    WorklogReport,
    WorklogReportRow,
)
from .results import HelperResult

_WORKLOG_FIELDS = ["summary", "project"]
_SEARCH_PAGE_SIZE = 5_000
_WORKLOG_PAGE_SIZE = 5_000


class WorklogHelpers:
    """High-level grouped helpers for Jira worklog CRUD and reporting."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def list(
        self,
        issue_key: str,
        *,
        start_at: int = 0,
        max_results: int = 50,
    ) -> HelperResult:
        """List worklogs on a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        if max_results < 1:
            raise JiraHelperValidationError("max_results must be at least 1.")

        try:
            data = self.api.worklogs.get_worklogs(
                issue_id=issue_key,
                start_at=start_at,
                max_results=min(max_results, _WORKLOG_PAGE_SIZE),
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch worklogs for {issue_key}: {exc}"
            ) from exc

        page = WorklogPage.model_validate(data)
        next_start = page.startAt + len(page.worklogs)
        return HelperResult.with_data(
            format_worklog_list(
                issue_key,
                page.worklogs,
                start_at=page.startAt,
                total=page.total,
                next_start=next_start,
            ),
            data,
        )

    def add(
        self,
        issue_key: str,
        time_spent: str,
        *,
        started: str | None = None,
        comment: str | None = None,
    ) -> HelperResult:
        """Add a worklog to a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        time_spent = require_non_empty_string(time_spent, field_name="time_spent")
        if started is not None:
            started = require_non_empty_string(started, field_name="started")
        if comment is not None:
            comment = require_non_empty_string(comment, field_name="comment")

        try:
            data = self.api.worklogs.add_worklog(
                issue_id=issue_key,
                time_spent=time_spent,
                started=started,
                comment=markdown_to_adf(comment) if comment is not None else None,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to add worklog to {issue_key}: {exc}"
            ) from exc

        worklog = JiraWorklog.model_validate(data)
        text = f"Added worklog to {issue_key}\n\n{format_worklog(worklog)}"
        return HelperResult.with_data(text, data)

    def update(
        self,
        issue_key: str,
        worklog_id: str,
        *,
        time_spent: str | None = None,
        started: str | None = None,
        comment: str | None = None,
    ) -> HelperResult:
        """Update an existing Jira worklog."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        worklog_id = require_non_empty_string(worklog_id, field_name="worklog_id")
        if time_spent is not None:
            time_spent = require_non_empty_string(time_spent, field_name="time_spent")
        if started is not None:
            started = require_non_empty_string(started, field_name="started")
        if comment is not None:
            comment = require_non_empty_string(comment, field_name="comment")
        if time_spent is None and started is None and comment is None:
            raise JiraHelperValidationError(
                "At least one of time_spent, started, or comment must be provided."
            )

        try:
            data = self.api.worklogs.update_worklog(
                issue_id=issue_key,
                worklog_id=worklog_id,
                time_spent=time_spent,
                started=started,
                comment=markdown_to_adf(comment) if comment is not None else None,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to update worklog {worklog_id} on {issue_key}: {exc}"
            ) from exc

        worklog = JiraWorklog.model_validate(data)
        text = (
            f"Updated worklog {worklog_id} on {issue_key}\n\n{format_worklog(worklog)}"
        )
        return HelperResult.with_data(text, data)

    def delete(self, issue_key: str, worklog_id: str) -> HelperResult:
        """Delete a Jira worklog."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        worklog_id = require_non_empty_string(worklog_id, field_name="worklog_id")

        try:
            self.api.worklogs.delete_worklog(
                issue_id=issue_key,
                worklog_id=worklog_id,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to delete worklog {worklog_id} from {issue_key}: {exc}"
            ) from exc

        data = {
            "status": "deleted",
            "issue_key": issue_key,
            "worklog_id": worklog_id,
        }
        return HelperResult.with_data(
            f"Deleted worklog {worklog_id} from {issue_key}",
            data,
        )

    def report(
        self,
        *,
        start_date: str,
        end_date: str,
        jql: str,
        account_id: str | None = None,
        max_issues: int = 100,
        include_details: bool = False,
    ) -> HelperResult:
        """Build a worklog report for issues selected by JQL."""
        jql = require_non_empty_string(jql, field_name="jql")
        if account_id is not None:
            account_id = require_non_empty_string(account_id, field_name="account_id")
        if max_issues < 1:
            raise JiraHelperValidationError("max_issues must be at least 1.")

        start_dt, exclusive_end_dt = validate_date_range(
            start_date=start_date,
            end_date=end_date,
        )
        issues, selector = self._search_report_issues(jql=jql, max_issues=max_issues)

        rows: list[WorklogReportRow] = []
        for issue in issues:
            rows.extend(
                self._collect_issue_rows(
                    issue=issue,
                    start_dt=start_dt,
                    exclusive_end_dt=exclusive_end_dt,
                    account_id=account_id,
                    include_details=include_details,
                )
            )

        rows.sort(key=lambda row: (row.dateTime, row.issueKey, row.worklogId or ""))
        total_seconds = sum(row.timeSpentSeconds or 0 for row in rows)
        report = WorklogReport(
            startDate=start_date,
            endDate=end_date,
            timezone="UTC",
            endDateInclusive=True,
            startedAtOrAfter=_format_utc(start_dt),
            startedBefore=_format_utc(exclusive_end_dt),
            accountId=account_id,
            issueSelector=selector,
            rowCount=len(rows),
            totalSeconds=total_seconds,
            totalHours=_seconds_to_hours(total_seconds),
            rows=rows,
        )
        data = report.model_dump(mode="json")
        return HelperResult.with_data(format_worklog_report(report), data)

    def _search_report_issues(
        self,
        *,
        jql: str,
        max_issues: int,
    ) -> tuple[Sequence[JiraIssue], WorklogIssueSelector]:
        issues: list[JiraIssue] = []
        next_page_token: str | None = None
        total: int | None = None

        while len(issues) < max_issues:
            remaining = max_issues - len(issues)
            try:
                data = self.api.search.enhanced_search(
                    jql=jql,
                    next_page_token=next_page_token,
                    max_results=min(remaining, _SEARCH_PAGE_SIZE),
                    fields=_WORKLOG_FIELDS,
                )
            except Exception as exc:
                raise JiraHelperOperationError(
                    f"Failed to search issues for worklog report: {exc}"
                ) from exc

            result = SearchResult.model_validate(data)
            total = result.total if result.total is not None else total
            if not result.issues:
                next_page_token = result.nextPageToken
                break

            issues.extend(result.issues[:remaining])
            next_page_token = result.nextPageToken
            if not next_page_token:
                break

        selector = WorklogIssueSelector(
            jql=jql,
            maxIssues=max_issues,
            issuesReturned=len(issues),
            truncated=bool(next_page_token)
            or (total is not None and len(issues) < total),
            nextPageToken=next_page_token,
            total=total,
        )
        return issues, selector

    def _collect_issue_rows(
        self,
        *,
        issue: JiraIssue,
        start_dt: datetime,
        exclusive_end_dt: datetime,
        account_id: str | None,
        include_details: bool,
    ) -> Sequence[WorklogReportRow]:
        rows: list[WorklogReportRow] = []
        start_at = 0
        issue_identifier = issue.id or issue.key
        started_after = _to_started_after_millis(start_dt)
        started_before = _to_epoch_millis(exclusive_end_dt)

        while True:
            try:
                data = self.api.worklogs.get_worklogs(
                    issue_id=issue_identifier,
                    start_at=start_at,
                    max_results=_WORKLOG_PAGE_SIZE,
                    extra_params={
                        "startedAfter": started_after,
                        "startedBefore": started_before,
                    },
                )
            except Exception as exc:
                raise JiraHelperOperationError(
                    f"Failed to fetch worklogs for {issue.key}: {exc}"
                ) from exc

            page = WorklogPage.model_validate(data)
            if not page.worklogs:
                break

            for worklog in page.worklogs:
                row = _build_row(
                    issue=issue,
                    worklog=worklog,
                    start_dt=start_dt,
                    exclusive_end_dt=exclusive_end_dt,
                    account_id=account_id,
                    include_details=include_details,
                )
                if row is not None:
                    rows.append(row)

            start_at = page.startAt + len(page.worklogs)
            if start_at >= page.total:
                break

        return rows


def _build_row(
    *,
    issue: JiraIssue,
    worklog: JiraWorklog,
    start_dt: datetime,
    exclusive_end_dt: datetime,
    account_id: str | None,
    include_details: bool,
) -> WorklogReportRow | None:
    started_dt = _parse_jira_datetime(worklog.started)
    if started_dt is None or not (start_dt <= started_dt < exclusive_end_dt):
        return None

    author = worklog.author
    author_account_id = author.accountId if author else ""
    if account_id is not None and author_account_id != account_id:
        return None

    return WorklogReportRow(
        dateTime=_format_utc(started_dt),
        issueId=issue.id or worklog.issueId,
        issueKey=issue.key,
        accountId=author_account_id,
        displayName=author.displayName if author else "Unknown",
        timeSpentHours=_seconds_to_hours(worklog.timeSpentSeconds),
        worklogId=worklog.id or None,
        issueSummary=issue.fields.summary,
        projectKey=issue.fields.project.key if issue.fields.project else None,
        started=_format_optional_utc(worklog.started),
        created=_format_optional_utc(worklog.created),
        updated=_format_optional_utc(worklog.updated),
        timeSpentSeconds=worklog.timeSpentSeconds,
        timeSpent=worklog.timeSpent,
        updateAuthor=worklog.updateAuthor if include_details else None,
        visibility=worklog.visibility if include_details else None,
        comment=worklog.comment if include_details else None,
        properties=worklog.properties if include_details else None,
    )


def _parse_jira_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    elif (
        len(normalized) >= 5 and normalized[-5] in {"+", "-"} and normalized[-3] != ":"
    ):
        normalized = normalized[:-2] + ":" + normalized[-2:]

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_optional_utc(value: str | None) -> str | None:
    parsed = _parse_jira_datetime(value)
    return _format_utc(parsed) if parsed else value


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _seconds_to_hours(seconds: int) -> float:
    return round(seconds / 3600, 2)


def _to_epoch_millis(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _to_started_after_millis(value: datetime) -> int:
    epoch_millis = _to_epoch_millis(value)
    return epoch_millis - 1 if epoch_millis > 0 else 0


__all__ = ["WorklogHelpers"]
