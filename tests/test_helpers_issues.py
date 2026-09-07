from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import httpx
import pytest

import jira2py.helpers.issues as issues_module
from jira2py import JiraAPI
from jira2py.api.issue_fields import IssueFields
from jira2py.api.issues import Issues
from jira2py.exceptions import JiraConnectionError
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.issues import IssueHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        issues=Mock(),
        fields=Mock(),
    )


def test_issue_helpers_do_not_expose_issue_read() -> None:
    assert not hasattr(IssueHelpers, "read")


def test_create_converts_description_and_markdown_fields(monkeypatch) -> None:
    api = _make_api()
    api.issues.create_issue.return_value = {"key": "PROJ-123"}
    helper = IssueHelpers(cast(JiraAPI, api))

    monkeypatch.setattr(
        issues_module,
        "convert_markdown_fields",
        lambda fields, adf_field_ids: {
            "customfield_10001": {"converted": fields["customfield_10001"]},
            "labels": fields["labels"],
        },
    )
    monkeypatch.setattr(
        helper,
        "_get_adf_field_ids",
        lambda: {"customfield_10001"},
    )
    monkeypatch.setattr(
        issues_module,
        "markdown_to_adf",
        lambda text: {"type": "doc", "markdown": text},
    )

    result = helper.create(
        "PROJ",
        "Bug",
        "Fix thing",
        description="Body",
        fields={"customfield_10001": "Extra details", "labels": ["backend"]},
    )

    api.issues.create_issue.assert_called_once_with(
        fields={
            "customfield_10001": {"converted": "Extra details"},
            "labels": ["backend"],
            "project": {"key": "PROJ"},
            "issuetype": {"name": "Bug"},
            "summary": "Fix thing",
            "description": {"type": "doc", "markdown": "Body"},
        }
    )
    assert result.text == (
        "Created PROJ-123: Fix thing\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )
    assert result.data == {"key": "PROJ-123"}


def test_issue_helpers_convert_jira_mentions_on_adf_write_fields() -> None:
    api = _make_api()
    api.issues.create_issue.return_value = {"key": "PROJ-123"}
    api.fields.get_fields.return_value = [
        {
            "id": "customfield_10001",
            "schema": {
                "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
            },
        }
    ]
    helper = IssueHelpers(cast(JiraAPI, api))
    mention = "[~ACCOUNTID:557057:User:AbC]"
    mention_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "mention", "attrs": {"id": "557057:User:AbC"}}],
            }
        ],
    }

    helper.create(
        "PROJ",
        "Bug",
        "Fix thing",
        description=mention,
        fields={
            "environment": mention,
            "customfield_10001": mention,
            "labels": ["backend"],
        },
    )
    helper.edit(
        "PROJ-123",
        description=mention,
        fields={"environment": mention, "customfield_10001": mention},
    )

    api.issues.create_issue.assert_called_once_with(
        fields={
            "environment": mention_adf,
            "customfield_10001": mention_adf,
            "labels": ["backend"],
            "project": {"key": "PROJ"},
            "issuetype": {"name": "Bug"},
            "summary": "Fix thing",
            "description": mention_adf,
        }
    )
    api.issues.edit_issue.assert_called_once_with(
        issue_id="PROJ-123",
        fields={
            "environment": mention_adf,
            "customfield_10001": mention_adf,
            "description": mention_adf,
        },
        return_issue=False,
    )
    assert api.fields.get_fields.call_count == 2


def test_create_rejects_conflicting_description_field() -> None:
    api = _make_api()
    helper = IssueHelpers(cast(JiraAPI, api))

    with pytest.raises(
        JiraHelperValidationError,
        match="Use explicit parameters instead of fields for: description",
    ):
        helper.create(
            "PROJ",
            "Bug",
            "Fix thing",
            description="Body",
            fields={"description": {"type": "doc"}},
        )

    api.fields.get_fields.assert_not_called()
    api.issues.create_issue.assert_not_called()


def test_create_raises_when_adf_field_metadata_lookup_fails() -> None:
    api = _make_api()
    api.fields.get_fields.side_effect = RuntimeError("metadata boom")
    helper = IssueHelpers(cast(JiraAPI, api))

    with pytest.raises(
        JiraHelperOperationError,
        match="Failed to fetch Jira field metadata needed for Markdown-to-ADF conversion",
    ) as exc_info:
        helper.create(
            "PROJ",
            "Bug",
            "Fix thing",
            fields={"customfield_10001": "Extra details"},
        )

    api.issues.create_issue.assert_not_called()
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == "metadata boom"


def test_edit_raw_response_handles_empty_response_body() -> None:
    api = _make_api()
    api.issues.edit_issue.return_value = None

    result = IssueHelpers(cast(JiraAPI, api)).edit(
        "PROJ-123", summary="Updated", raw=True
    )

    api.issues.edit_issue.assert_called_once_with(
        issue_id="PROJ-123",
        fields={"summary": "Updated"},
        return_issue=True,
    )
    assert result.data is None
    assert result.raw_content == "null"
    assert result.text == (
        "Successfully updated PROJ-123\n"
        "URL: https://example.atlassian.net/browse/PROJ-123"
    )


def test_issue_edit_timeout_is_marked_as_uncertain_delivery() -> None:
    api = _make_api()
    api.issues.edit_issue.side_effect = JiraConnectionError("request timed out")

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit("PROJ-123", summary="Updated")

    assert "may have applied the mutation" in str(exc_info.value)
    assert "must reread" in str(exc_info.value)
    assert exc_info.value.details == {
        "stage": "mutation_request",
        "issue_key": "PROJ-123",
        "mutation_may_have_succeeded": True,
    }
    assert isinstance(exc_info.value.__cause__, JiraConnectionError)
    api.issues.edit_issue.assert_called_once()


def test_issue_edit_remote_protocol_error_is_marked_as_uncertain_delivery(
    make_client,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.RemoteProtocolError("peer disconnected")

    client = make_client(handler)
    api = SimpleNamespace(
        credentials=client.credentials,
        issues=Issues(client),
        fields=Mock(),
    )

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit("PROJ-123", summary="Updated")

    assert exc_info.value.details == {
        "stage": "mutation_request",
        "issue_key": "PROJ-123",
        "mutation_may_have_succeeded": True,
    }
    assert isinstance(exc_info.value.__cause__, JiraConnectionError)
    assert len(requests) == 1
    assert requests[0].method == "PUT"
    assert requests[0].url.path == "/rest/api/3/issue/PROJ-123"


def test_preflight_remote_protocol_error_is_an_ordinary_failure(make_client) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise httpx.RemoteProtocolError("peer disconnected")

    client = make_client(handler)
    api = SimpleNamespace(
        credentials=client.credentials,
        issues=Issues(client),
        fields=IssueFields(client),
    )

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-123", fields={"environment": "Body"}
        )

    assert "Failed to fetch Jira field metadata" in str(exc_info.value)
    assert exc_info.value.details == {}
    assert isinstance(exc_info.value.__cause__, JiraConnectionError)
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/rest/api/3/field"


def test_preflight_connection_failure_is_not_marked_as_uncertain_delivery() -> None:
    api = _make_api()
    api.fields.get_fields.side_effect = JiraConnectionError("request timed out")

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-123", fields={"environment": "Body"}
        )

    assert "Failed to fetch Jira field metadata" in str(exc_info.value)
    assert exc_info.value.details == {}
    api.issues.edit_issue.assert_not_called()


def test_transition_keeps_name_selector_compatibility_and_is_unverified() -> None:
    api = _make_api()
    api.issues.get_transitions.return_value = {
        "transitions": [
            {
                "id": "11",
                "name": "Start Progress",
                "to": {"name": "In Progress"},
            }
        ]
    }

    result = IssueHelpers(cast(JiraAPI, api)).transition(
        "PROJ-123",
        "start progress",
    )

    api.issues.get_transitions.assert_called_once_with(issue_id="PROJ-123")
    api.issues.get_issue.assert_not_called()
    api.issues.transition_issue.assert_called_once_with(
        issue_id="PROJ-123",
        transition_id="11",
    )
    assert result.data == {
        "issue_key": "PROJ-123",
        "transition_id": "11",
        "transition_name": "Start Progress",
        "to_status": "In Progress",
        "status": "transitioned",
        "verified": False,
    }
    assert (
        'Jira accepted transition "Start Progress" (id: 11) for PROJ-123 '
        "without a verification read"
    ) in result.text
    assert "Expected destination status: In Progress" in result.text


def test_transition_forwards_jira_native_fields_and_update_without_echoing_them() -> (
    None
):
    api = _make_api()
    api.issues.get_transitions.return_value = {
        "transitions": [{"id": "21", "name": "Resolve Issue"}]
    }
    raw_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "mention", "attrs": {"id": "raw:ID"}}],
            }
        ],
    }
    fields = {"resolution": {"name": "Done"}, "customfield_10001": raw_adf}
    fields_before = deepcopy(fields)
    update = {"labels": [{"add": "released"}]}

    result = IssueHelpers(cast(JiraAPI, api)).transition(
        "PROJ-123",
        "21",
        fields=fields,
        update=update,
    )

    api.issues.transition_issue.assert_called_once_with(
        issue_id="PROJ-123",
        transition_id="21",
        fields=fields,
        update=update,
    )
    api.issues.get_issue.assert_not_called()
    assert fields == fields_before
    assert (
        api.issues.transition_issue.call_args.kwargs["fields"]["customfield_10001"]
        is raw_adf
    )
    assert result.data is not None
    assert "fields" not in result.data
    assert "update" not in result.data
    assert "resolution" not in result.text
    assert "released" not in result.text


def test_transition_rejects_overlapping_fields_and_update_before_jira_requests() -> (
    None
):
    api = _make_api()

    with pytest.raises(
        JiraHelperValidationError,
        match="A field cannot appear in both fields and update: resolution",
    ):
        IssueHelpers(cast(JiraAPI, api)).transition(
            "PROJ-123",
            "21",
            fields={"resolution": {"name": "Done"}},
            update={"resolution": [{"set": {"name": "Done"}}]},
        )

    api.issues.get_transitions.assert_not_called()
    api.issues.transition_issue.assert_not_called()


def test_transition_rejects_unknown_transition_with_available_options() -> None:
    api = _make_api()
    api.issues.get_transitions.return_value = {
        "transitions": [
            {"id": "11", "name": "Start Progress"},
            {"id": "21", "name": "Close Issue"},
        ]
    }

    with pytest.raises(
        JiraHelperValidationError,
        match='Transition "Done" is not available for PROJ-123',
    ) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).transition("PROJ-123", "Done")

    assert "Start Progress (id: 11), Close Issue (id: 21)" in str(exc_info.value)
    api.issues.transition_issue.assert_not_called()


def test_validate_methods_reject_invalid_issue_input() -> None:
    helper = IssueHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="project_key"):
        helper.validate_create("   ", "Bug", "Summary")

    with pytest.raises(JiraHelperValidationError, match="Nothing to update"):
        helper.validate_edit("PROJ-123")

    with pytest.raises(JiraHelperValidationError, match="summary"):
        helper.validate_create(
            "PROJ",
            "Bug",
            "Summary",
            fields={"summary": "duplicate"},
        )
