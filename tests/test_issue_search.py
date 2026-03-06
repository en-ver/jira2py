"""Tests for IssueSearch API."""

import httpx
import pytest

from jira2py.api.issue_search import IssueSearch, IssueSearchAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_SEARCH_RESPONSE = {
    "issues": [
        {"id": "10000", "key": "TEST-1", "fields": {"summary": "Test issue"}},
        {"id": "10001", "key": "TEST-2", "fields": {"summary": "Another issue"}},
    ],
    "total": 2,
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


class TestIssueSearch:
    """Tests for sync IssueSearch API."""

    def test_enhanced_search(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_SEARCH_RESPONSE)

        api = IssueSearch(_make_sync_client(test_credentials, handler))
        result = api.enhanced_search(jql="project = TEST")

        assert result["total"] == 2
        assert result["issues"][0]["key"] == "TEST-1"

    def test_enhanced_search_with_fields(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_SEARCH_RESPONSE)

        api = IssueSearch(_make_sync_client(test_credentials, handler))
        result = api.enhanced_search(
            jql="project = TEST",
            fields=["summary", "status"],
            max_results=10,
        )

        assert result["total"] == 2


class TestIssueSearchAsync:
    """Tests for async IssueSearch API."""

    @pytest.mark.asyncio
    async def test_enhanced_search(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_SEARCH_RESPONSE)

        api = IssueSearchAsync(_make_async_client(test_credentials, handler))
        result = await api.enhanced_search(jql="project = TEST")

        assert result["total"] == 2
        assert result["issues"][0]["key"] == "TEST-1"
