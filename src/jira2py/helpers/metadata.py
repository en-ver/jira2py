"""Grouped metadata helper operations for jira2py."""

from __future__ import annotations

from jira2py.api import JiraAPI

from ._text import format_field_metadata, format_issue_type_list
from ._validation import require_non_empty_string
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import FieldMeta, IssueType, JiraUser, ProjectSearchResult
from .results import HelperResult


class MetadataHelpers:
    """High-level grouped helpers for Jira metadata and discovery."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

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


__all__ = ["MetadataHelpers"]
