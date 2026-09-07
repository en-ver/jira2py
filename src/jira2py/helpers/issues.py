"""Grouped issue helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from adf_bridge import AdfBridgeError

from jira2py.api import JiraAPI

from ._adf import convert_markdown_fields, detect_adf_field_ids, markdown_to_adf
from ._managed_media import (
    _JiraMarkdownWriteSession,
    _PreparedMarkdownDocument,
    _validate_create_markdown_images,
)
from ._validation import require_non_empty_string, validate_field_conflicts
from .errors import (
    JiraHelperOperationError,
    JiraHelperValidationError,
    _mutation_request_error,
)
from .models import IssueTransition
from .results import HelperResult

_CREATE_FIELD_CONFLICTS = frozenset({"project", "issuetype", "summary"})
_EDIT_FIELD_CONFLICTS = frozenset({"summary", "description"})


class IssueHelpers:
    """High-level grouped helpers for Jira issues."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

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

        try:
            extra_fields = self._prepare_markdown_fields(
                fields,
                reserved_fields=_CREATE_FIELD_CONFLICTS,
                reject_create_attachment_images=True,
            )
            if description:
                _validate_create_markdown_images(self.api, [description])
                extra_fields["description"] = markdown_to_adf(description)
        except AdfBridgeError as exc:
            raise JiraHelperValidationError(
                "Markdown input cannot be converted to Jira rich text."
            ) from exc

        issue_fields: dict[str, Any] = {
            **extra_fields,
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
        }

        try:
            data = self.api.issues.create_issue(fields=issue_fields)
        except Exception as exc:
            raise _mutation_request_error(
                exc,
                ordinary_message=f"Failed to create issue: {exc}",
                target=f"project:{project_key}",
            ) from exc

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

        session = _JiraMarkdownWriteSession(self.api, issue_key)
        update_fields, managed_documents = self._prepare_edit_markdown_fields(
            fields,
            session=session,
        )
        if summary:
            update_fields["summary"] = summary
        if description:
            prepared = session.prepare(description)
            update_fields["description"] = prepared.document
            if prepared.has_managed_images:
                managed_documents["description"] = prepared

        try:
            data = self.api.issues.edit_issue(
                issue_id=issue_key,
                fields=update_fields,
                return_issue=raw,
            )
        except Exception as exc:
            raise _mutation_request_error(
                exc,
                ordinary_message=f"Failed to update issue {issue_key}: {exc}",
                issue_key=issue_key,
            ) from exc

        if managed_documents:
            self._verify_managed_issue_readback(
                issue_key,
                session=session,
                managed_documents=managed_documents,
            )

        text = (
            f"Successfully updated {issue_key}\n"
            f"URL: {self.api.credentials.url}/browse/{issue_key}"
        )
        if not raw:
            return HelperResult.text_only(text)
        if data is None:
            return HelperResult(text=text, raw_content="null")
        return HelperResult.with_data(text, data)

    def transition(
        self,
        issue_key: str,
        transition: str,
        *,
        fields: Mapping[str, Any] | None = None,
        update: Mapping[str, Any] | None = None,
    ) -> HelperResult:
        """Transition an issue by ID or name with Jira-native field operations."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        transition = require_non_empty_string(transition, field_name="transition")
        overlapping_fields = set(fields or {}).intersection(update or {})
        if overlapping_fields:
            overlap = ", ".join(sorted(map(str, overlapping_fields)))
            raise JiraHelperValidationError(
                "A field cannot appear in both fields and update: " + overlap
            )
        resolved = self._resolve_transition(issue_key, transition)

        transition_kwargs: dict[str, Any] = {
            "issue_id": issue_key,
            "transition_id": resolved.id,
        }
        if fields is not None:
            transition_kwargs["fields"] = fields
        if update is not None:
            transition_kwargs["update"] = update

        try:
            self.api.issues.transition_issue(**transition_kwargs)
        except Exception as exc:
            raise _mutation_request_error(
                exc,
                ordinary_message=f"Failed to transition issue {issue_key}: {exc}",
                issue_key=issue_key,
                target=f"transition:{resolved.id}",
            ) from exc

        data = {
            "issue_key": issue_key,
            "transition_id": resolved.id,
            "transition_name": resolved.name,
            "to_status": resolved.to.name if resolved.to else None,
            "status": "transitioned",
            "verified": False,
        }
        text_lines = [
            f'Jira accepted transition "{resolved.name}" (id: {resolved.id}) for '
            f"{issue_key} without a verification read"
        ]
        if resolved.to:
            text_lines.append(f"Expected destination status: {resolved.to.name}")
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
        reject_create_attachment_images: bool = False,
    ) -> dict[str, Any]:
        extra_fields = dict(fields or {})
        validate_field_conflicts(extra_fields, reserved_fields=reserved_fields)
        if not extra_fields:
            return extra_fields
        adf_field_ids = self._get_adf_field_ids()
        if reject_create_attachment_images:
            _validate_create_markdown_images(
                self.api,
                (
                    value
                    for field_id, value in extra_fields.items()
                    if field_id in adf_field_ids and isinstance(value, str)
                ),
            )
        return convert_markdown_fields(extra_fields, adf_field_ids)

    def _prepare_edit_markdown_fields(
        self,
        fields: Mapping[str, Any] | None,
        *,
        session: _JiraMarkdownWriteSession,
    ) -> tuple[dict[str, Any], dict[str, _PreparedMarkdownDocument]]:
        extra_fields = dict(fields or {})
        validate_field_conflicts(extra_fields, reserved_fields=_EDIT_FIELD_CONFLICTS)
        if not extra_fields:
            return extra_fields, {}

        adf_field_ids = self._get_adf_field_ids()
        managed_documents: dict[str, _PreparedMarkdownDocument] = {}
        for field_id, value in extra_fields.items():
            if field_id not in adf_field_ids or not isinstance(value, str):
                continue
            prepared = session.prepare(value)
            extra_fields[field_id] = prepared.document
            if prepared.has_managed_images:
                managed_documents[field_id] = prepared
        return extra_fields, managed_documents

    def _verify_managed_issue_readback(
        self,
        issue_key: str,
        *,
        session: _JiraMarkdownWriteSession,
        managed_documents: Mapping[str, _PreparedMarkdownDocument],
    ) -> None:
        try:
            persisted_issue = self.api.issues.get_issue(
                issue_id=issue_key,
                fields=list(managed_documents),
            )
            persisted_fields = persisted_issue.get("fields")
            if not isinstance(persisted_fields, dict):
                raise JiraHelperOperationError(
                    "Jira did not return fields for managed image verification."
                )
            for field_id, prepared in managed_documents.items():
                session.verify(prepared, persisted_fields.get(field_id))
        except Exception as exc:
            raise JiraHelperOperationError(
                "Jira may have applied the issue update, but managed image readback "
                "verification failed. Reread the issue before retrying.",
                details={
                    "stage": "persisted_readback",
                    "issue_key": issue_key,
                    "mutation_may_have_succeeded": True,
                },
            ) from exc

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
