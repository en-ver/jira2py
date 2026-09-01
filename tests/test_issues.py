"""Tests for Issues API."""

import json
from typing import Any, cast
from unittest.mock import Mock

import httpx
import pytest

from jira2py.api.issues import Issues

SAMPLE_ISSUE = {
    "id": "10000",
    "key": "TEST-1",
    "fields": {"summary": "Test issue", "status": {"name": "Open"}},
}

SAMPLE_CHANGELOGS = {
    "startAt": 0,
    "maxResults": 50,
    "total": 1,
    "isLast": True,
    "values": [
        {
            "id": "100",
            "items": [
                {"field": "status", "fromString": "Open", "toString": "In Progress"}
            ],
        },
    ],
}

SAMPLE_CHANGELOGS_BY_IDS = {
    "histories": [
        {
            "id": "100",
            "created": "2026-01-02T03:04:05.000+0000",
            "items": [
                {"field": "status", "fromString": "Open", "toString": "In Progress"}
            ],
        }
    ],
    "startAt": 0,
    "maxResults": 50,
    "total": 1,
}

SAMPLE_EDIT_META = {
    "fields": {
        "summary": {"required": True, "name": "Summary"},
        "priority": {"required": False, "name": "Priority"},
    }
}

SAMPLE_CREATE_ISSUE_TYPES = {
    "issueTypes": [
        {"id": "10000", "name": "Task"},
        {"id": "10001", "name": "Bug"},
    ]
}

SAMPLE_CREATE_FIELDS = {
    "fields": [
        {"fieldId": "summary", "required": True},
        {"fieldId": "issuetype", "required": True},
    ]
}

SAMPLE_TRANSITIONS = {
    "transitions": [
        {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
        {"id": "21", "name": "Close Issue", "to": {"name": "Done"}},
    ]
}

SAMPLE_CREATED_ISSUE = {
    "id": "10002",
    "key": "TEST-3",
    "self": "https://test.atlassian.net/rest/api/3/issue/10002",
}


class TestIssues:
    """Tests for Issues API."""

    def test_get_issue_omits_unset_fields_and_expand(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "fields" not in request.url.params
            assert "expand" not in request.url.params
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(make_client(handler))
        result = api.get_issue("TEST-1")

        assert result["key"] == "TEST-1"
        assert result["fields"]["summary"] == "Test issue"

    def test_get_issue_serializes_exact_field_sequence_without_expand(
        self, make_client
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["fields"] == (
                "summary,*navigable,-description,summary"
            )
            assert "expand" not in request.url.params
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(make_client(handler))
        api.get_issue(
            "TEST-1",
            fields=("summary", "*navigable", "-description", "summary"),
        )

    def test_get_issue_allows_raw_extra_fields_when_fields_is_none(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["fields"] == "*all,-description"
            assert "expand" not in request.url.params
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(make_client(handler))
        api.get_issue(
            "TEST-1",
            extra_params={"fields": "*all,-description"},
        )

    def test_get_issue_extra_params_fields_take_precedence(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["fields"] == "*all,-description"
            assert request.url.params["expand"] == "renderedFields"
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(make_client(handler))
        api.get_issue(
            "TEST-1",
            fields=["summary", "status"],
            expand="renderedFields",
            extra_params={"fields": "*all,-description"},
        )

    @pytest.mark.parametrize(
        ("fields", "error"),
        [
            ("summary,status", TypeError),
            (b"summary", TypeError),
            (42, TypeError),
            ([], ValueError),
            ((), ValueError),
            (["summary", 7], TypeError),
            ([""], ValueError),
            (["   "], ValueError),
            ([" summary"], ValueError),
            (["summary "], ValueError),
            (["summary,status"], ValueError),
        ],
    )
    def test_get_issue_rejects_invalid_field_sequences(
        self,
        fields: object,
        error: type[Exception],
    ) -> None:
        client = Mock()
        api = Issues(client)

        with pytest.raises(error):
            api.get_issue("TEST-1", fields=cast(Any, fields))

        client._request_jira.assert_not_called()

    def test_get_changelogs(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert request.url.path == "/rest/api/3/issue/TEST-1/changelog"
            assert request.url.params["startAt"] == "0"
            assert request.url.params["maxResults"] == "50"
            return httpx.Response(200, json=SAMPLE_CHANGELOGS)

        api = Issues(make_client(handler))
        result = api.get_changelogs("TEST-1")

        assert result["total"] == 1
        assert result["isLast"] is True
        assert len(result["values"]) == 1
        assert result["values"][0]["items"][0]["field"] == "status"

    def test_get_changelogs_by_ids_posts_page_response(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/rest/api/3/issue/TEST-1/changelog/list"
            assert json.loads(request.content) == {"changelogIds": [100, 101]}
            return httpx.Response(200, json=SAMPLE_CHANGELOGS_BY_IDS)

        api = Issues(make_client(handler))
        result = api.get_changelogs_by_ids("TEST-1", [100, 101])

        assert result == SAMPLE_CHANGELOGS_BY_IDS

    def test_get_changelogs_by_ids_forwards_and_allows_raw_overrides(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["expand"] == "properties"
            assert json.loads(request.content) == {"changelogIds": [202]}
            return httpx.Response(200, json=SAMPLE_CHANGELOGS_BY_IDS)

        api = Issues(make_client(handler))
        api.get_changelogs_by_ids(
            "TEST-1",
            [100],
            extra_params={"expand": "properties"},
            extra_data={"changelogIds": [202]},
        )

    def test_edit_issue_returns_none_on_204(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        api = Issues(make_client(handler))
        result = api.edit_issue("TEST-1", fields={"summary": "Updated"})

        assert result is None

    def test_edit_issue_returns_issue_when_requested(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(make_client(handler))
        result = api.edit_issue(
            "TEST-1", fields={"summary": "Updated"}, return_issue=True
        )

        assert result is not None
        assert result["key"] == "TEST-1"

    def test_get_edit_metadata(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_EDIT_META)

        api = Issues(make_client(handler))
        result = api.get_edit_metadata("TEST-1")

        assert "summary" in result["fields"]

    def test_get_transitions(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/transitions"
            assert request.url.params["expand"] == "transitions.fields"
            assert request.url.params["transitionId"] == "21"
            assert "includeUnavailableTransitions" not in request.url.params
            assert "skipRemoteOnlyCondition" not in request.url.params
            assert "sortByOpsBarAndStatus" not in request.url.params
            return httpx.Response(200, json=SAMPLE_TRANSITIONS)

        api = Issues(make_client(handler))
        result = api.get_transitions(
            "TEST-1",
            expand="transitions.fields",
            transition_id="21",
        )

        assert len(result["transitions"]) == 2
        assert result["transitions"][1]["name"] == "Close Issue"

    def test_get_transitions_serializes_named_controls_with_legacy_positions(
        self, make_client
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["expand"] == "transitions.fields"
            assert request.url.params["transitionId"] == "34"
            assert request.url.params["includeUnavailableTransitions"] == "true"
            assert request.url.params["skipRemoteOnlyCondition"] == "false"
            assert request.url.params["sortByOpsBarAndStatus"] == "true"
            return httpx.Response(200, json=SAMPLE_TRANSITIONS)

        api = Issues(make_client(handler))
        api.get_transitions(
            "TEST-1",
            "transitions.fields",
            "21",
            {"transitionId": "34"},
            include_unavailable_transitions=True,
            skip_remote_only_condition=False,
            sort_by_ops_bar_and_status=True,
        )

    def test_transition_issue_returns_none_on_204(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/transitions"
            assert request.method == "POST"
            assert json.loads(request.content) == {
                "transition": {"id": "21"},
                "fields": {"resolution": {"name": "Done"}},
                "update": {"labels": [{"add": "released"}]},
            }
            return httpx.Response(204)

        api = Issues(make_client(handler))
        result = api.transition_issue(
            "TEST-1",
            transition_id="21",
            fields={"resolution": {"name": "Done"}},
            update={"labels": [{"add": "released"}]},
        )

        assert result is None

    def test_get_create_issue_types(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_CREATE_ISSUE_TYPES)

        api = Issues(make_client(handler))
        result = api.get_create_issue_types("TEST")

        assert len(result["issueTypes"]) == 2
        assert result["issueTypes"][0]["name"] == "Task"

    def test_get_create_fields(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_CREATE_FIELDS)

        api = Issues(make_client(handler))
        result = api.get_create_fields("TEST", "10000")

        assert len(result["fields"]) == 2

    def test_create_issue(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_CREATED_ISSUE)

        api = Issues(make_client(handler))
        result = api.create_issue(
            fields={
                "summary": "New issue",
                "project": {"key": "TEST"},
                "issuetype": {"name": "Task"},
            }
        )

        assert result["key"] == "TEST-3"
