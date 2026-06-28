"""Tests for Issue Worklogs API."""

import json

import httpx
import pytest

from jira2py import JiraAPI
from jira2py.api.api_base import _DEFAULT_PAGE_SIZE
from jira2py.api.issue_worklogs import IssueWorklogs

SAMPLE_WORKLOG = {
    "id": "10000",
    "issueId": "10001",
    "started": "2026-06-25T09:00:00.000+0000",
    "timeSpent": "1h",
    "timeSpentSeconds": 3600,
    "author": {"accountId": "user-1", "displayName": "Test User"},
}

SAMPLE_WORKLOGS = {
    "startAt": 0,
    "maxResults": _DEFAULT_PAGE_SIZE,
    "total": 1,
    "worklogs": [SAMPLE_WORKLOG],
}


class TestIssueWorklogs:
    """Tests for Issue Worklogs API."""

    def test_get_worklogs_returns_raw_response_and_path(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/worklog"
            assert request.url.params["startAt"] == "0"
            assert request.url.params["maxResults"] == str(_DEFAULT_PAGE_SIZE)
            return httpx.Response(200, json=SAMPLE_WORKLOGS)

        api = IssueWorklogs(make_client(handler))
        result = api.get_worklogs("TEST-1")

        assert result == SAMPLE_WORKLOGS

    def test_get_worklogs_allows_extra_params_and_overrides_named_params(
        self, make_client
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["startAt"] == "3"
            assert request.url.params["maxResults"] == "7"
            assert request.url.params["startedAfter"] == "1719273600000"
            assert request.url.params["startedBefore"] == "1719360000000"
            assert request.url.params["expand"] == "properties"
            return httpx.Response(200, json=SAMPLE_WORKLOGS)

        api = IssueWorklogs(make_client(handler))
        result = api.get_worklogs(
            "TEST-1",
            start_at=10,
            max_results=25,
            extra_params={
                "startAt": 3,
                "maxResults": 7,
                "startedAfter": 1719273600000,
                "startedBefore": 1719360000000,
                "expand": "properties",
            },
        )

        assert result["worklogs"][0]["id"] == "10000"

    def test_get_worklogs_raises_type_error_for_non_dict_response(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[{"id": "10000"}])

        api = IssueWorklogs(make_client(handler))

        with pytest.raises(TypeError, match="Expected dict response"):
            api.get_worklogs("TEST-1")

    def test_add_worklog_posts_time_started_and_comment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/worklog"
            assert request.method == "POST"
            assert json.loads(request.content.decode()) == {
                "timeSpent": "1h",
                "started": "2026-06-25T09:00:00.000+0000",
                "comment": {"type": "doc", "content": []},
            }
            return httpx.Response(201, json=SAMPLE_WORKLOG)

        api = IssueWorklogs(make_client(handler))
        result = api.add_worklog(
            "TEST-1",
            "1h",
            started="2026-06-25T09:00:00.000+0000",
            comment={"type": "doc", "content": []},
        )

        assert result == SAMPLE_WORKLOG

    def test_update_worklog_puts_issue_scoped_worklog_fields(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/worklog/10000"
            assert request.method == "PUT"
            assert json.loads(request.content.decode()) == {
                "timeSpent": "2h",
                "started": "2026-06-25T10:00:00.000+0000",
                "comment": {"type": "doc", "content": []},
            }
            return httpx.Response(200, json=SAMPLE_WORKLOG)

        api = IssueWorklogs(make_client(handler))
        result = api.update_worklog(
            "TEST-1",
            "10000",
            time_spent="2h",
            started="2026-06-25T10:00:00.000+0000",
            comment={"type": "doc", "content": []},
        )

        assert result == SAMPLE_WORKLOG

    def test_delete_worklog_uses_issue_scoped_delete_endpoint(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/worklog/10000"
            assert request.method == "DELETE"
            return httpx.Response(204)

        api = IssueWorklogs(make_client(handler))

        assert api.delete_worklog("TEST-1", "10000") is None


class TestJiraAPIWorklogsFacade:
    """Tests for JiraAPI worklogs facade."""

    def test_worklogs_property_is_cached(self):
        jira = JiraAPI(
            url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test-token",
        )

        first = jira.worklogs
        second = jira.worklogs

        assert isinstance(first, IssueWorklogs)
        assert first is second
