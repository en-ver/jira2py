"""Grouped metadata helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from jira2py.api import JiraAPI

from ._text import (
    format_field_catalog,
    format_field_metadata,
    format_issue_type_list,
    format_priority_list,
    format_project,
    format_status_list,
    format_transition_list,
)
from ._validation import (
    require_non_empty_string,
    validate_canonical_field_ids,
)
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import (
    FieldMeta,
    IssueTransition,
    IssueType,
    JiraPriority,
    JiraProject,
    JiraStatus,
    JiraUser,
    ProjectSearchResult,
)
from .results import HelperResult


class MetadataHelpers:
    """High-level grouped helpers for Jira metadata and discovery."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def list_fields(
        self,
        project_key: str | None = None,
        *,
        query: str | None = None,
        field_ids: Sequence[str] | None = None,
        field_types: Sequence[str] | None = None,
        start_at: int = 0,
        max_results: int = 20,
    ) -> HelperResult:
        """Get one searchable Jira field catalog page.

        ``project_key`` supplies Jira's project context filter only. It does not
        identify fields applicable to a particular issue type or create/edit screen.
        """
        project_key = _validate_optional_project_key(project_key)
        normalized_query = _normalize_optional_query(query)
        normalized_field_ids = validate_canonical_field_ids(field_ids)
        normalized_field_types = _validate_field_types(field_types)
        start_at = _validate_non_negative_integer(start_at, field_name="start_at")
        max_results = _validate_positive_integer(max_results, field_name="max_results")

        project_ids: list[int] | None = None
        if project_key is not None:
            try:
                project_data = self.api.projects.get_project(
                    project_id_or_key=project_key
                )
            except Exception as exc:
                raise JiraHelperOperationError(
                    f"Failed to fetch project {project_key}: {exc}"
                ) from exc
            project_ids = [_project_id_from_data(project_data)]

        try:
            data = self.api.fields.search_fields(
                start_at=start_at,
                max_results=max_results,
                query=normalized_query,
                field_ids=normalized_field_ids,
                field_types=normalized_field_types,
                project_ids=project_ids,
            )
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to fetch fields: {exc}") from exc

        values = _field_values_from_page(data)
        return HelperResult.with_data(
            format_field_catalog(values, project_key=project_key),
            data,
        )

    def issue_types(self, project_key: str) -> HelperResult:
        """List issue types available for project issue creation."""
        project_key = require_non_empty_string(project_key, field_name="project_key")
        issue_types_raw = self._get_issue_types_raw(project_key)
        issue_types = [
            IssueType.model_validate(issue_type) for issue_type in issue_types_raw
        ]
        return HelperResult.with_data(
            format_issue_type_list(project_key, issue_types),
            issue_types_raw,
        )

    def create_fields(self, project_key: str, issue_type: str) -> HelperResult:
        """Get create-screen field metadata for a project issue type."""
        project_key = require_non_empty_string(project_key, field_name="project_key")
        issue_type = require_non_empty_string(issue_type, field_name="issue_type")
        issue_types_raw = self._get_issue_types_raw(project_key)
        issue_types = [
            IssueType.model_validate(issue_type_data)
            for issue_type_data in issue_types_raw
        ]
        matched = next(
            (
                available_type
                for available_type in issue_types
                if available_type.name.lower() == issue_type.lower()
            ),
            None,
        )
        if matched is None:
            available = ", ".join(available_type.name for available_type in issue_types)
            raise JiraHelperValidationError(
                f'Issue type "{issue_type}" not found in {project_key}. '
                f"Available: {available}"
            )

        try:
            fields_data = self.api.issues.get_create_fields(
                project_id_or_key=project_key,
                issue_type_id=matched.id,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch create fields for {project_key}/{matched.name}: {exc}"
            ) from exc

        fields_raw = fields_data.get("values", fields_data.get("fields", []))
        fields_list = [FieldMeta.model_validate(field) for field in fields_raw]
        return HelperResult.with_data(
            format_field_metadata(project_key, matched.name, fields_list),
            fields_raw,
        )

    def edit_fields(self, issue_key: str) -> HelperResult:
        """Get edit-screen field metadata for an existing Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")

        try:
            edit_data = self.api.issues.get_edit_metadata(issue_id=issue_key)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch edit metadata for {issue_key}: {exc}"
            ) from exc

        fields_dict = edit_data.get("fields", {})
        fields_list = [
            FieldMeta.model_validate({"fieldId": field_id, **meta})
            for field_id, meta in fields_dict.items()
        ]
        return HelperResult.with_data(
            format_field_metadata(issue_key, "edit", fields_list),
            edit_data,
        )

    def transitions(
        self,
        issue_key: str,
        *,
        transition_id: str | None = None,
        include_unavailable_transitions: bool | None = None,
    ) -> HelperResult:
        """Discover an issue's transitions with Jira-native screen metadata."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        if transition_id is not None:
            transition_id = require_non_empty_string(
                transition_id,
                field_name="transition_id",
            )

        try:
            data = self.api.issues.get_transitions(
                issue_id=issue_key,
                expand="transitions.fields",
                transition_id=transition_id,
                include_unavailable_transitions=include_unavailable_transitions,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch transitions for {issue_key}: {exc}"
            ) from exc

        transitions = [
            IssueTransition.model_validate(transition)
            for transition in data.get("transitions", [])
        ]
        return HelperResult.with_data(
            format_transition_list(issue_key, transitions),
            data,
        )

    def project(self, project_id_or_key: str) -> HelperResult:
        """Get a single Jira project by explicit key or ID."""
        project_id_or_key = require_non_empty_string(
            project_id_or_key,
            field_name="project_id_or_key",
        )

        try:
            data = self.api.projects.get_project(project_id_or_key=project_id_or_key)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch project {project_id_or_key}: {exc}"
            ) from exc

        project = JiraProject.model_validate(data)
        return HelperResult.with_data(format_project(project), data)

    def projects(self, query: str | None = None) -> HelperResult:
        """List Jira projects accessible to the current user."""
        normalized_query = query.strip() if query is not None else None
        normalized_query = normalized_query or None

        try:
            data = self.api.projects.search_projects(
                query=normalized_query,
                max_results=100,
                extra_params={"orderBy": "name"},
            )
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to fetch projects: {exc}") from exc

        result = ProjectSearchResult.model_validate(data)
        if not result.values:
            if normalized_query:
                text = f'No projects found matching "{normalized_query}"'
            else:
                text = "No projects found"
            return HelperResult.with_data(text, data)

        lines: list[str] = []
        header = (
            f'Projects matching "{normalized_query}"'
            if normalized_query
            else "Projects"
        )
        lines.append(f"{header}:\n")
        for project in result.values:
            lines.append(f"  {project.key} — {project.name}")

        if not result.isLast:
            if result.total is not None:
                more = result.total - len(result.values)
                lines.append(f"\n  ... and {more} more (refine your search)")
            else:
                lines.append("\n  ... more results available (refine your search)")

        return HelperResult.with_data("\n".join(lines), data)

    def statuses(self) -> HelperResult:
        """List Jira statuses visible to the current user."""
        try:
            data = self.api.metadata.get_statuses()
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to fetch statuses: {exc}") from exc

        statuses = [JiraStatus.model_validate(status) for status in data]
        return HelperResult.with_data(format_status_list(statuses), data)

    def priorities(self) -> HelperResult:
        """List Jira priorities visible to the current user."""
        try:
            data = self.api.metadata.get_priorities()
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch priorities: {exc}"
            ) from exc

        priorities = [JiraPriority.model_validate(priority) for priority in data]
        return HelperResult.with_data(format_priority_list(priorities), data)

    def users(self, query: str, *, max_results: int = 10) -> HelperResult:
        """Search Jira users by name or email."""
        query = require_non_empty_string(query, field_name="query")
        limit = min(max_results, 50)

        try:
            data = self.api.users.search_users(query=query, max_results=limit)
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to search users: {exc}") from exc

        user_list = [JiraUser.model_validate(user) for user in data]
        if not user_list:
            return HelperResult.with_data(f"No users found matching: {query}", data)

        lines = [f"Found {len(user_list)} user(s):\n"]
        for user in user_list:
            status = " (inactive)" if not user.active else ""
            lines.append(f"- {user.displayName}{status} — accountId: {user.accountId}")
        return HelperResult.with_data("\n".join(lines), data)

    def _get_issue_types_raw(self, project_key: str) -> list[dict[str, object]]:
        try:
            type_data = self.api.issues.get_create_issue_types(
                project_id_or_key=project_key
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch issue types for {project_key}: {exc}"
            ) from exc
        issue_types = type_data.get("values", type_data.get("issueTypes", []))
        return list(issue_types)


def _validate_optional_project_key(project_key: str | None) -> str | None:
    if project_key is None:
        return None
    return require_non_empty_string(project_key, field_name="project_key")


def _normalize_optional_query(query: str | None) -> str | None:
    if query is None:
        return None
    if not isinstance(query, str):
        raise JiraHelperValidationError("query must be a string.")
    return query.strip() or None


def _validate_field_types(
    field_types: Sequence[str] | None,
) -> list[str] | None:
    if field_types is None:
        return None
    if isinstance(field_types, (str, bytes, bytearray)) or not isinstance(
        field_types, Sequence
    ):
        raise JiraHelperValidationError(
            "field_types must be a non-empty sequence of system or custom."
        )
    if not field_types:
        raise JiraHelperValidationError("field_types must not be empty.")

    normalized = list(field_types)
    if any(
        not isinstance(field_type, str) or field_type not in {"system", "custom"}
        for field_type in normalized
    ):
        raise JiraHelperValidationError(
            "field_types must contain only system or custom."
        )
    return [str(field_type) for field_type in normalized]


def _validate_non_negative_integer(value: int, *, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise JiraHelperValidationError(f"{field_name} must be a non-negative integer.")
    return value


def _validate_positive_integer(value: int, *, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise JiraHelperValidationError(f"{field_name} must be at least 1.")
    return value


def _project_id_from_data(data: object) -> int:
    if not isinstance(data, Mapping):
        raise JiraHelperOperationError("Jira returned malformed project data.")
    project_data = cast(Mapping[str, Any], data)
    project_id = project_data.get("id")
    if (
        isinstance(project_id, int)
        and not isinstance(project_id, bool)
        and project_id >= 0
    ):
        return project_id
    if isinstance(project_id, str) and project_id.isdecimal():
        return int(project_id)
    raise JiraHelperOperationError("Jira returned a project without a numeric ID.")


def _field_values_from_page(data: object) -> list[Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        raise JiraHelperOperationError("Jira returned a malformed field page.")
    page_data = cast(Mapping[str, Any], data)
    values = page_data.get("values")
    if not isinstance(values, list) or not all(
        isinstance(value, Mapping) for value in values
    ):
        raise JiraHelperOperationError("Jira returned a malformed field page.")

    fields = cast(list[Mapping[str, Any]], values)
    if any(
        not isinstance(field.get("id"), str) or not field["id"].strip()
        for field in fields
    ):
        raise JiraHelperOperationError("Jira returned a malformed field page.")
    return fields


__all__ = ["MetadataHelpers"]
