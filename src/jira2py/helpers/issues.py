"""Grouped issue helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from jira2py.api import JiraAPI

from ._adf import convert_markdown_fields, detect_adf_field_ids, markdown_to_adf
from ._text import DEFAULT_FIELDS, format_issue_full
from ._validation import require_non_empty_string, validate_field_conflicts
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import IssueTransition, JiraIssue
from .results import HelperResult

_CREATE_FIELD_CONFLICTS = frozenset({"project", "issuetype", "summary"})
_EDIT_FIELD_CONFLICTS = frozenset({"summary", "description"})


class IssueHelpers:
    """High-level grouped helpers for Jira issues."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def read(
        self,
        issue_key: str,
        *,
        extra_fields: Sequence[str] | None = None,
    ) -> HelperResult:
        """Read a Jira issue and return readable plus structured output."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        request_fields = list(DEFAULT_FIELDS)
        if extra_fields:
            request_fields.extend(
                field for field in extra_fields if field not in request_fields
            )

        try:
            data = self.api.issues.get_issue(
                issue_id=issue_key,
                fields=",".join(request_fields),
                expand="names",
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch issue {issue_key}: {exc}"
            ) from exc

        issue = JiraIssue.model_validate(data)
        names = data.get("names") or {}
        text = format_issue_full(
            issue,
            url=f"{self.api.credentials.url}/browse/{issue_key}",
            requested_fields=request_fields,
            field_names=names,
        )
        return HelperResult.with_data(text, data)

    def create(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        *,
        description: str | None = None,
        fields: Mapping[str, Any] | None = None,
    ) -> HelperResult:
        """Create a Jira issue."""
        self.validate_create(
            project_key,
            issue_type,
            summary,
            description=description,
            fields=fields,
        )

        issue_fields: dict[str, Any] = {
            **self._prepare_markdown_fields(
                fields,
                reserved_fields=_CREATE_FIELD_CONFLICTS,
            ),
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
        }
        if description:
            issue_fields["description"] = markdown_to_adf(description)

        try:
            data = self.api.issues.create_issue(fields=issue_fields)
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to create issue: {exc}") from exc

        key = data.get("key", "?")
        text = f"Created {key}: {summary}\nURL: {self.api.credentials.url}/browse/{key}"
        return HelperResult.with_data(text, data)

    def edit(
        self,
        issue_key: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        fields: Mapping[str, Any] | None = None,
        raw: bool = False,
    ) -> HelperResult:
        """Update an existing Jira issue."""
        self.validate_edit(
            issue_key,
            summary=summary,
            description=description,
            fields=fields,
        )

        update_fields = self._prepare_markdown_fields(
            fields,
            reserved_fields=_EDIT_FIELD_CONFLICTS,
        )
        if summary:
            update_fields["summary"] = summary
        if description:
            update_fields["description"] = markdown_to_adf(description)

        try:
            data = self.api.issues.edit_issue(
                issue_id=issue_key,
                fields=update_fields,
                return_issue=raw,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to update issue {issue_key}: {exc}"
            ) from exc

        text = (
            f"Successfully updated {issue_key}\n"
            f"URL: {self.api.credentials.url}/browse/{issue_key}"
        )
        if not raw:
            return HelperResult.text_only(text)
        if data is None:
            return HelperResult(text=text, raw_content="null")
        return HelperResult.with_data(text, data)

    def transition(self, issue_key: str, transition: str) -> HelperResult:
        """Transition an issue using an explicit transition ID or name."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        transition = require_non_empty_string(transition, field_name="transition")
        resolved = self._resolve_transition(issue_key, transition)

        try:
            self.api.issues.transition_issue(
                issue_id=issue_key,
                transition_id=resolved.id,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to transition issue {issue_key}: {exc}"
            ) from exc

        data = {
            "issue_key": issue_key,
            "transition_id": resolved.id,
            "transition_name": resolved.name,
            "to_status": resolved.to.name if resolved.to else None,
            "status": "transitioned",
        }
        text_lines = [
            f'Applied transition "{resolved.name}" (id: {resolved.id}) to {issue_key}'
        ]
        if resolved.to:
            text_lines.append(f"Target Status: {resolved.to.name}")
        text_lines.append(f"URL: {self.api.credentials.url}/browse/{issue_key}")
        return HelperResult.with_data("\n".join(text_lines), data)

    def validate_create(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        *,
        description: str | None = None,
        fields: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate create-issue input without performing Jira API calls."""
        require_non_empty_string(project_key, field_name="project_key")
        require_non_empty_string(issue_type, field_name="issue_type")
        require_non_empty_string(summary, field_name="summary")
        validate_field_conflicts(fields, reserved_fields=_CREATE_FIELD_CONFLICTS)
        if description is not None:
            validate_field_conflicts(fields, reserved_fields={"description"})

    def validate_edit(
        self,
        issue_key: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        fields: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate edit-issue input without performing Jira API calls."""
        require_non_empty_string(issue_key, field_name="issue_key")
        if not summary and not description and not fields:
            raise JiraHelperValidationError(
                "Nothing to update. Provide at least one of: summary, "
                "description, or fields."
            )
        validate_field_conflicts(fields, reserved_fields=_EDIT_FIELD_CONFLICTS)

    def _resolve_transition(
        self,
        issue_key: str,
        transition: str,
    ) -> IssueTransition:
        try:
            data = self.api.issues.get_transitions(issue_id=issue_key)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch transitions for {issue_key}: {exc}"
            ) from exc

        transitions = [
            IssueTransition.model_validate(item) for item in data.get("transitions", [])
        ]
        if not transitions:
            raise JiraHelperValidationError(
                f"No transitions are available for {issue_key}."
            )

        by_id = [item for item in transitions if item.id == transition]
        if len(by_id) == 1:
            return by_id[0]

        by_exact_name = [item for item in transitions if item.name == transition]
        if len(by_exact_name) == 1:
            return by_exact_name[0]
        if len(by_exact_name) > 1:
            raise JiraHelperValidationError(
                f'Ambiguous transition name "{transition}" for {issue_key}. '
                f"Matching IDs: {', '.join(item.id for item in by_exact_name)}"
            )

        normalized = transition.casefold()
        by_name = [item for item in transitions if item.name.casefold() == normalized]
        if len(by_name) == 1:
            return by_name[0]
        if len(by_name) > 1:
            raise JiraHelperValidationError(
                f'Ambiguous transition name "{transition}" for {issue_key}. '
                f"Matching IDs: {', '.join(item.id for item in by_name)}"
            )

        available = ", ".join(f"{item.name} (id: {item.id})" for item in transitions)
        raise JiraHelperValidationError(
            f'Transition "{transition}" is not available for {issue_key}. '
            f"Available transitions: {available}"
        )

    def _prepare_markdown_fields(
        self,
        fields: Mapping[str, Any] | None,
        *,
        reserved_fields: frozenset[str],
    ) -> dict[str, Any]:
        extra_fields = dict(fields or {})
        validate_field_conflicts(extra_fields, reserved_fields=reserved_fields)
        if not extra_fields:
            return extra_fields
        return convert_markdown_fields(extra_fields, self._get_adf_field_ids())

    def _get_adf_field_ids(self) -> set[str]:
        try:
            all_fields = self.api.fields.get_fields()
        except Exception as exc:
            raise JiraHelperOperationError(
                "Failed to fetch Jira field metadata needed for Markdown-to-ADF "
                f"conversion: {exc}"
            ) from exc
        return detect_adf_field_ids(all_fields)


__all__ = ["IssueHelpers"]
