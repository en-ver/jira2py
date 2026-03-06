"""Tests for Issues API."""

import httpx
import pytest

from jira2py.api.issues import Issues, IssuesAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_ISSUE = {
    "id": "10000",
    "key": "TEST-1",
    "fields": {"summary": "Test issue", "status": {"name": "Open"}},
}

SAMPLE_CHANGELOGS = [
    {
        "id": "100",
        "items": [{"field": "status", "fromString": "Open", "toString": "In Progress"}],
    },
]

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

SAMPLE_CREATED_ISSUE = {
    "id": "10002",
    "key": "TEST-3",
    "self": "https://test.atlassian.net/rest/api/3/issue/10002",
}


def _make_sync_client(test_credentials, handler):
    client = JiraClientSync(credentials=test_credentials)
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    return client


def _make_async_client(test_credentials, handler):
    client = JiraClientAsync(credentials=test_credentials)
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    return client


class TestIssues:
    """Tests for sync Issues API."""

    def test_get_issue(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.get_issue("TEST-1")

        assert result["key"] == "TEST-1"
        assert result["fields"]["summary"] == "Test issue"

    def test_get_changelogs(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_CHANGELOGS)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.get_changelogs("TEST-1")

        assert len(result) == 1
        assert result[0]["items"][0]["field"] == "status"

    def test_edit_issue_returns_none_on_204(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            # Jira returns 204 No Content when return_issue=False (default)
            return httpx.Response(204)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.edit_issue("TEST-1", fields={"summary": "Updated"})

        assert result is None

    def test_edit_issue_returns_issue_when_requested(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            # Jira returns 200 with body when return_issue=True
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.edit_issue(
            "TEST-1", fields={"summary": "Updated"}, return_issue=True
        )

        assert result is not None
        assert result["key"] == "TEST-1"

    def test_get_edit_metadata(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_EDIT_META)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.get_edit_metadata("TEST-1")

        assert "summary" in result["fields"]

    def test_get_create_issue_types(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_CREATE_ISSUE_TYPES)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.get_create_issue_types("TEST")

        assert len(result["issueTypes"]) == 2
        assert result["issueTypes"][0]["name"] == "Task"

    def test_get_create_fields(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_CREATE_FIELDS)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.get_create_fields("TEST", "10000")

        assert len(result["fields"]) == 2

    def test_create_issue(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_CREATED_ISSUE)

        api = Issues(_make_sync_client(test_credentials, handler))
        result = api.create_issue(
            fields={
                "summary": "New issue",
                "project": {"key": "TEST"},
                "issuetype": {"name": "Task"},
            }
        )

        assert result["key"] == "TEST-3"


class TestIssuesAsync:
    """Tests for async Issues API."""

    @pytest.mark.asyncio
    async def test_get_issue(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = IssuesAsync(_make_async_client(test_credentials, handler))
        result = await api.get_issue("TEST-1")

        assert result["key"] == "TEST-1"
        assert result["fields"]["summary"] == "Test issue"

    @pytest.mark.asyncio
    async def test_create_issue(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_CREATED_ISSUE)

        api = IssuesAsync(_make_async_client(test_credentials, handler))
        result = await api.create_issue(
            fields={
                "summary": "New issue",
                "project": {"key": "TEST"},
                "issuetype": {"name": "Task"},
            }
        )

        assert result["key"] == "TEST-3"

    @pytest.mark.asyncio
    async def test_edit_issue_returns_none_on_204(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        api = IssuesAsync(_make_async_client(test_credentials, handler))
        result = await api.edit_issue("TEST-1", fields={"summary": "Updated"})

        assert result is None

    @pytest.mark.asyncio
    async def test_edit_issue_returns_issue_when_requested(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ISSUE)

        api = IssuesAsync(_make_async_client(test_credentials, handler))
        result = await api.edit_issue(
            "TEST-1", fields={"summary": "Updated"}, return_issue=True
        )

        assert result is not None
        assert result["key"] == "TEST-1"
