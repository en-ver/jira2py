"""Tests for IssueFields API."""

import httpx
import pytest

from jira2py.api.issue_fields import IssueFields, IssueFieldsAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_FIELDS_RESPONSE = [
    {"id": "summary", "name": "Summary", "custom": False, "schema": {"type": "string"}},
    {
        "id": "customfield_10001",
        "name": "Story Points",
        "custom": True,
        "schema": {"type": "number"},
    },
]


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


class TestIssueFields:
    """Tests for sync IssueFields API."""

    def test_get_fields(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_FIELDS_RESPONSE)

        api = IssueFields(_make_sync_client(test_credentials, handler))
        result = api.get_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
        assert result[1]["custom"] is True


class TestIssueFieldsAsync:
    """Tests for async IssueFields API."""

    @pytest.mark.asyncio
    async def test_get_fields(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_FIELDS_RESPONSE)

        api = IssueFieldsAsync(_make_async_client(test_credentials, handler))
        result = await api.get_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
