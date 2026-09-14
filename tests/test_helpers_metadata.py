from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, call

import pytest

from jira2py import JiraAPI
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.metadata import MetadataHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        issues=Mock(),
        fields=Mock(),
        metadata=Mock(),
        projects=Mock(),
        users=Mock(),
    )


def test_list_fields_returns_one_raw_jira_page_and_canonical_id_text() -> None:
    api = _make_api()
    page = {
        "startAt": 4,
        "maxResults": 2,
        "total": 8,
        "isLast": False,
        "values": [
            {"id": "summary", "key": "different-key", "name": "Summary"},
            {"id": "customfield_10001", "name": "Story Points", "custom": True},
        ],
    }
    api.fields.search_fields.return_value = page

    result = MetadataHelpers(cast(JiraAPI, api)).list_fields(
        query="  points  ",
        field_ids=["summary", "customfield_10001"],
        field_types=["system", "custom"],
        start_at=4,
        max_results=2,
    )

    api.fields.search_fields.assert_called_once_with(
        start_at=4,
        max_results=2,
        query="points",
        field_ids=["summary", "customfield_10001"],
        field_types=["system", "custom"],
        project_ids=None,
    )
    api.projects.get_project.assert_not_called()
    assert result.data is page
    assert result.text == (
        "Jira field catalog: 2 returned\n\n"
        "- Summary (id: summary)\n"
        "- Story Points (id: customfield_10001)"
    )


def test_list_fields_resolves_project_key_to_numeric_context_id() -> None:
    api = _make_api()
    api.projects.get_project.return_value = {"id": "10000", "key": "PROJ"}
    api.fields.search_fields.return_value = {
        "startAt": 0,
        "maxResults": 20,
        "total": 0,
        "isLast": True,
        "values": [],
    }

    result = MetadataHelpers(cast(JiraAPI, api)).list_fields("PROJ")

    api.projects.get_project.assert_called_once_with(project_id_or_key="PROJ")
    api.fields.search_fields.assert_called_once_with(
        start_at=0,
        max_results=20,
        query=None,
        field_ids=None,
        field_types=None,
        project_ids=[10000],
    )
    assert result.text == "No Jira fields found for project context PROJ"


def test_list_fields_rejects_invalid_inputs_before_jira_requests() -> None:
    api = _make_api()
    helper = MetadataHelpers(cast(JiraAPI, api))

    with pytest.raises(JiraHelperValidationError, match="project_key"):
        helper.list_fields("   ")
    with pytest.raises(JiraHelperValidationError, match="query"):
        helper.list_fields(query=cast(Any, 42))
    with pytest.raises(JiraHelperValidationError, match="field_ids"):
        helper.list_fields(field_ids=cast(Any, "summary"))
    with pytest.raises(JiraHelperValidationError, match="field_ids"):
        helper.list_fields(field_ids=[" summary"])
    with pytest.raises(JiraHelperValidationError, match="field_types"):
        helper.list_fields(field_types=["SYSTEM"])
    with pytest.raises(JiraHelperValidationError, match="start_at"):
        helper.list_fields(start_at=-1)
    with pytest.raises(JiraHelperValidationError, match="max_results"):
        helper.list_fields(max_results=0)

    api.projects.get_project.assert_not_called()
    api.fields.search_fields.assert_not_called()


def test_list_fields_rejects_malformed_project_or_field_page() -> None:
    api = _make_api()
    api.projects.get_project.return_value = {"id": "not-numeric"}
    helper = MetadataHelpers(cast(JiraAPI, api))

    with pytest.raises(JiraHelperOperationError, match="numeric ID"):
        helper.list_fields("PROJ")
    api.fields.search_fields.assert_not_called()

    api = _make_api()
    api.fields.search_fields.return_value = {"values": [{"name": "Summary"}]}
    with pytest.raises(JiraHelperOperationError, match="malformed field page"):
        MetadataHelpers(cast(JiraAPI, api)).list_fields()


def test_issue_types_formats_project_create_types() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "startAt": 0,
        "isLast": True,
        "values": [
            {"id": "10000", "name": "Task"},
            {"id": "10001", "name": "Sub-task", "subtask": True},
        ],
    }

    result = MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")

    api.issues.get_create_issue_types.assert_called_once_with(
        project_id_or_key="PROJ",
        start_at=0,
    )
    assert result.data == api.issues.get_create_issue_types.return_value["values"]
    assert "Issue types for PROJ:" in result.text
    assert "Task (id: 10000)" in result.text
    assert "Sub-task (id: 10001) (subtask)" in result.text


def test_issue_types_aggregates_canonical_pages_in_jira_order() -> None:
    api = _make_api()
    first = {"id": "10000", "name": "Task", "unknown": {"preserved": True}}
    second = {"id": "10001", "name": "Bug"}
    api.issues.get_create_issue_types.side_effect = [
        {
            "startAt": 10,
            "isLast": False,
            "total": 1,
            "values": [first],
        },
        {
            "startAt": 11,
            "isLast": True,
            "total": 1,
            "values": [second],
        },
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")

    assert result.data == [first, second]
    assert isinstance(result.data, list)
    assert result.data[0] is first
    assert api.issues.get_create_issue_types.call_args_list == [
        call(project_id_or_key="PROJ", start_at=0),
        call(project_id_or_key="PROJ", start_at=11),
    ]


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
        start_at=0,
    )
    assert result.data == api.issues.get_create_fields.return_value["fields"]
    assert "Fields for PROJ / Bug:" in result.text
    assert "Required:" in result.text
    assert "Optional:" in result.text


def test_create_fields_stops_after_the_first_matching_type_page() -> None:
    api = _make_api()
    first_field = {"fieldId": "summary", "name": "Summary", "required": True}
    second_field = {"fieldId": "priority", "name": "Priority", "required": False}
    api.issues.get_create_issue_types.side_effect = [
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"id": "10000", "name": "Bug"}],
        },
        {
            "startAt": 1,
            "isLast": False,
            "values": [{"id": "10001", "name": "Task"}],
        },
    ]
    api.issues.get_create_fields.side_effect = [
        {"startAt": 0, "isLast": False, "values": [first_field]},
        {"startAt": 1, "isLast": True, "values": [second_field]},
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "tAsK")

    assert result.data == [first_field, second_field]
    assert api.issues.get_create_issue_types.call_args_list == [
        call(project_id_or_key="PROJ", start_at=0),
        call(project_id_or_key="PROJ", start_at=1),
    ]
    assert api.issues.get_create_fields.call_args_list == [
        call(project_id_or_key="PROJ", issue_type_id="10001", start_at=0),
        call(project_id_or_key="PROJ", issue_type_id="10001", start_at=1),
    ]


def test_create_fields_rejects_a_matching_non_advancing_issue_type_page() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.side_effect = [
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"id": "10000", "name": "Bug"}],
        },
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"id": "10001", "name": "Task"}],
        },
    ]

    with pytest.raises(
        JiraHelperOperationError, match="create issue-type page.*did not advance"
    ):
        MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")

    assert api.issues.get_create_issue_types.call_args_list == [
        call(project_id_or_key="PROJ", start_at=0),
        call(project_id_or_key="PROJ", start_at=1),
    ]
    api.issues.get_create_fields.assert_not_called()


def test_create_fields_aggregates_paginated_fields_fallback() -> None:
    api = _make_api()
    first = {"fieldId": "summary", "name": "Summary", "required": True}
    second = {"fieldId": "priority", "name": "Priority", "required": False}
    api.issues.get_create_issue_types.return_value = {
        "issueTypes": [{"id": "10001", "name": "Task"}]
    }
    api.issues.get_create_fields.side_effect = [
        {"startAt": 0, "isLast": False, "fields": [first]},
        {"startAt": 1, "isLast": True, "fields": [second]},
    ]

    result = MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")

    assert result.data == [first, second]
    assert api.issues.get_create_fields.call_args_list == [
        call(project_id_or_key="PROJ", issue_type_id="10001", start_at=0),
        call(project_id_or_key="PROJ", issue_type_id="10001", start_at=1),
    ]


@pytest.mark.parametrize(
    "page",
    [
        {"issueTypes": [], "total": 0},
        {"issueTypes": [], "startAt": 0},
        {"issueTypes": [], "startAt": 0, "isLast": "true"},
    ],
    ids=["total-only", "start-at-only", "invalid-is-last"],
)
def test_issue_types_rejects_partial_fallback_pagination(page: object) -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = page

    with pytest.raises(JiraHelperOperationError, match="create issue-type page"):
        MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")


@pytest.mark.parametrize(
    "page",
    [
        {"values": []},
        {
            "values": "not-a-list",
            "issueTypes": [{"id": "10001", "name": "Task"}],
        },
        {"values": [], "startAt": True, "isLast": True},
        {"values": ["not-a-mapping"], "startAt": 0, "isLast": True},
    ],
    ids=[
        "missing-pagination-metadata",
        "canonical-values-are-authoritative",
        "boolean-start-at",
        "non-mapping-item",
    ],
)
def test_issue_types_rejects_malformed_canonical_pages(page: object) -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = page

    with pytest.raises(JiraHelperOperationError, match="create issue-type page"):
        MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")


@pytest.mark.parametrize(
    ("second_page", "error_message"),
    [
        (RuntimeError("boom"), "Failed to fetch create issue-type page"),
        ({"values": []}, "malformed create issue-type page"),
    ],
    ids=["request-failure", "response-failure"],
)
def test_issue_types_fails_atomically_after_a_later_page_error(
    second_page: object,
    error_message: str,
) -> None:
    api = _make_api()
    api.issues.get_create_issue_types.side_effect = [
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"id": "10001", "name": "Task"}],
        },
        second_page,
    ]

    with pytest.raises(JiraHelperOperationError, match=error_message):
        MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")

    assert api.issues.get_create_issue_types.call_count == 2


def test_create_fields_rejects_a_non_advancing_page() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "startAt": 0,
        "isLast": True,
        "values": [{"id": "10001", "name": "Task"}],
    }
    api.issues.get_create_fields.side_effect = [
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"fieldId": "summary", "name": "Summary"}],
        },
        {"startAt": 1, "isLast": False, "values": []},
    ]

    with pytest.raises(
        JiraHelperOperationError, match="create-field page.*did not advance"
    ):
        MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")

    assert api.issues.get_create_fields.call_count == 2


def test_create_fields_rejects_unknown_issue_type_after_terminal_discovery() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.side_effect = [
        {
            "startAt": 0,
            "isLast": False,
            "values": [{"id": "10001", "name": "Bug"}],
        },
        {
            "startAt": 1,
            "isLast": True,
            "values": [{"id": "10002", "name": "Story"}],
        },
    ]

    with pytest.raises(JiraHelperValidationError, match='Issue type "Task" not found'):
        MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")

    assert api.issues.get_create_issue_types.call_args_list == [
        call(project_id_or_key="PROJ", start_at=0),
        call(project_id_or_key="PROJ", start_at=1),
    ]
    api.issues.get_create_fields.assert_not_called()


def test_create_metadata_rejects_invalid_arguments_before_requests() -> None:
    api = _make_api()
    helper = MetadataHelpers(cast(JiraAPI, api))

    with pytest.raises(JiraHelperValidationError, match="project_key"):
        helper.issue_types(" ")
    with pytest.raises(JiraHelperValidationError, match="project_key"):
        helper.create_fields(" ", "Task")
    with pytest.raises(JiraHelperValidationError, match="issue_type"):
        helper.create_fields("PROJ", " ")

    api.issues.get_create_issue_types.assert_not_called()
    api.issues.get_create_fields.assert_not_called()


def test_create_metadata_wraps_model_validation_errors() -> None:
    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "startAt": 0,
        "isLast": True,
        "values": [{"id": "10001", "name": ["not-a-name"]}],
    }

    with pytest.raises(
        JiraHelperOperationError, match="create issue-type page"
    ) as exc_info:
        MetadataHelpers(cast(JiraAPI, api)).issue_types("PROJ")

    assert exc_info.value.__cause__ is not None

    api = _make_api()
    api.issues.get_create_issue_types.return_value = {
        "startAt": 0,
        "isLast": True,
        "values": [{"id": "10001", "name": "Task"}],
    }
    api.issues.get_create_fields.return_value = {
        "startAt": 0,
        "isLast": True,
        "values": [{"fieldId": ["not-an-id"]}],
    }

    with pytest.raises(JiraHelperOperationError, match="create-field page") as exc_info:
        MetadataHelpers(cast(JiraAPI, api)).create_fields("PROJ", "Task")

    assert exc_info.value.__cause__ is not None


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


def test_transitions_returns_raw_expanded_metadata_with_agent_focused_text() -> None:
    api = _make_api()
    envelope = {
        "expand": "transitions.fields",
        "transitions": [
            {
                "id": "21",
                "name": "Resolve Issue",
                "to": {"id": "10001", "name": "Done"},
                "hasScreen": True,
                "isAvailable": False,
                "isConditional": True,
                "isGlobal": True,
                "looped": True,
                "fields": {
                    "resolution": {
                        "key": "resolution",
                        "name": "Resolution",
                        "required": True,
                        "operations": ["set"],
                        "schema": {"type": "resolution"},
                        "allowedValues": [{"id": "1", "name": "Done"}],
                        "defaultValue": {"id": "1", "name": "Done"},
                        "autoCompleteUrl": "https://example.test/complete",
                        "configuration": {"opaque": "value"},
                    }
                },
            }
        ],
    }
    api.issues.get_transitions.return_value = envelope

    result = MetadataHelpers(cast(JiraAPI, api)).transitions(
        "PROJ-1",
        transition_id="21",
        include_unavailable_transitions=True,
    )

    api.issues.get_transitions.assert_called_once_with(
        issue_id="PROJ-1",
        expand="transitions.fields",
        transition_id="21",
        include_unavailable_transitions=True,
    )
    assert result.data is envelope
    assert result.data["transitions"][0]["fields"]["resolution"]["configuration"] == {
        "opaque": "value"
    }
    assert "Transitions for PROJ-1:" in result.text
    assert "Resolve Issue (id: 21) → Done (status id: 10001)" in result.text
    assert (
        "available: no; screen: yes; conditional: yes; global: yes; looped: yes"
        in result.text
    )
    assert (
        "field: resolution; key: resolution; name: Resolution; required: yes; "
        "operations: set"
    ) in result.text


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
