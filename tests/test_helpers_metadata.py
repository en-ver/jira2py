from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperValidationError
from jira2py.helpers.metadata import MetadataHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        issues=Mock(),
        projects=Mock(),
        users=Mock(),
    )


def test_issue_types_formats_project_create_types() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "values": [
            {"id": "10000", "name": "Task"},
            {"id": "10001", "name": "Sub-task", "subtask": True},
        ]
    }

    result = MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")

    api.issues.get_create_issue_types.assert_called_once_with(project_id_or_key="PROJ")
    assert result.data == api.issues.get_create_issue_types.return_value["values"]
    assert "Issue types for PROJ:" in result.text
    assert "Task (id: 10000)" in result.text
    assert "Sub-task (id: 10001) (subtask)" in result.text


def test_create_fields_resolves_issue_type_case_insensitively() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "issueTypes": [{"id": "10001", "name": "Bug"}]
    }
    api.issues.get_create_fields.return_value = {
        "fields": [
            {"fieldId": "summary", "name": "Summary", "required": True},
            {"fieldId": "priority", "name": "Priority", "required": False},
        ]
    }

    result = MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "bug")

    api.issues.get_create_fields.assert_called_once_with(
        project_id_or_key="PROJ",
        issue_type_id="10001",
    )
    assert result.data == api.issues.get_create_fields.return_value["fields"]
    assert "Fields for PROJ / Bug:" in result.text
    assert "Required:" in result.text
    assert "Optional:" in result.text


def test_create_fields_rejects_unknown_issue_type() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "issueTypes": [{"id": "10001", "name": "Bug"}]
    }

    with pytest.raises(JiraHelperValidationError, match='Issue type "Task" not found'):
        MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")


def test_edit_fields_formats_edit_metadata() -> None:
    api = _make_api()
    api.issues.get_edit_metadata.return_value = {
        "fields": {
            "summary": {
                "name": "Summary",
                "required": True,
                "schema": {"type": "string"},
            }
        }
    }

    result = MetadataHelpers(cast(JiraAPI, api)).edit_fields("PROJ-1")

    api.issues.get_edit_metadata.assert_called_once_with(issue_id="PROJ-1")
    assert result.data == api.issues.get_edit_metadata.return_value
    assert "Fields for PROJ-1 / edit:" in result.text
    assert 'summary "Summary" — string' in result.text


def test_projects_formats_results_and_more_hint() -> None:
    api = _make_api()
    api.projects.search_projects.return_value = {
        "values": [{"key": "PROJ", "name": "Project One"}],
        "isLast": False,
        "total": 2,
    }

    result = MetadataHelpers(cast(JiraAPI, api)).projects("  proj  ")

    api.projects.search_projects.assert_called_once_with(
        query="proj",
        max_results=100,
        extra_params={"orderBy": "name"},
    )
    assert result.text == (
        'Projects matching "proj":\n\n'
        "  PROJ — Project One\n\n"
        "  ... and 1 more (refine your search)"
    )


def test_users_formats_results_and_clamps_limit() -> None:
    api = _make_api()
    api.users.search_users.return_value = [
        {"displayName": "Alice", "accountId": "a1", "active": True},
        {"displayName": "Bob", "accountId": "b2", "active": False},
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).users("alice", max_results=100)

    api.users.search_users.assert_called_once_with(query="alice", max_results=50)
    assert result.data == api.users.search_users.return_value
    assert result.text == (
        "Found 2 user(s):\n\n- Alice — accountId: a1\n- Bob (inactive) — accountId: b2"
    )
