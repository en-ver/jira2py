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
        metadata=Mock(),
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


def test_transitions_formats_ids_names_and_required_fields() -> None:
    api = _make_api()
    api.issues.get_transitions.return_value = {
        "transitions": [
            {
                "id": "11",
                "name": "Start Progress",
                "to": {"name": "In Progress"},
            },
            {
                "id": "21",
                "name": "Resolve Issue",
                "to": {"name": "Done"},
                "fields": {
                    "resolution": {"required": True},
                    "comment": {"required": False},
                },
            },
        ]
    }

    result = MetadataHelpers(cast(JiraAPI, api)).transitions("PROJ-1")

    api.issues.get_transitions.assert_called_once_with(
        issue_id="PROJ-1",
        expand="transitions.fields",
    )
    assert result.data == api.issues.get_transitions.return_value
    assert "Available transitions for PROJ-1:" in result.text
    assert "Start Progress (id: 11) → In Progress" in result.text
    assert "Resolve Issue (id: 21) → Done [required fields: resolution]" in result.text


def test_project_formats_single_project_details() -> None:
    api = _make_api()
    api.projects.get_project.return_value = {
        "id": "10000",
        "key": "PROJ",
        "name": "Project One",
        "projectTypeKey": "software",
        "style": "classic",
        "lead": {"displayName": "Alice", "accountId": "a1", "active": True},
        "description": "First project",
    }

    result = MetadataHelpers(cast(JiraAPI, api)).project("PROJ")

    api.projects.get_project.assert_called_once_with(project_id_or_key="PROJ")
    assert result.data == api.projects.get_project.return_value
    assert result.text == (
        "Project PROJ — Project One\n"
        "ID: 10000\n"
        "Type: software\n"
        "Style: classic\n"
        "Lead: Alice (a1)\n"
        "Description:\n"
        "First project"
    )


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


def test_statuses_formats_structured_status_list() -> None:
    api = _make_api()
    api.metadata.get_statuses.return_value = [
        {
            "id": "1",
            "name": "To Do",
            "description": "Initial status",
            "statusCategory": {"id": 2, "key": "new", "name": "To Do"},
        },
        {
            "id": "3",
            "name": "Done",
            "statusCategory": {"id": 3, "key": "done", "name": "Done"},
        },
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).statuses()

    api.metadata.get_statuses.assert_called_once_with()
    assert result.data == api.metadata.get_statuses.return_value
    assert result.text == (
        "Jira statuses: 2 total\n\n"
        "- To Do (id: 1) [category: To Do] — Initial status\n"
        "- Done (id: 3) [category: Done]"
    )


def test_priorities_formats_structured_priority_list() -> None:
    api = _make_api()
    api.metadata.get_priorities.return_value = [
        {
            "id": "1",
            "name": "Highest",
            "description": "Top urgency",
            "isDefault": False,
        },
        {
            "id": "5",
            "name": "Medium",
            "isDefault": True,
        },
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).priorities()

    api.metadata.get_priorities.assert_called_once_with()
    assert result.data == api.metadata.get_priorities.return_value
    assert result.text == (
        "Jira priorities: 2 total\n\n"
        "- Highest (id: 1) — Top urgency\n"
        "- Medium (id: 5) [default]"
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
