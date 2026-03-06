"""Tests for IssueLinks API."""

import httpx
import pytest

from jira2py.api.issue_links import IssueLinks, IssueLinksAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_LINK_TYPES_RESPONSE = {
    "issueLinkTypes": [
        {
            "id": "10000",
            "name": "Blocks",
            "inward": "is blocked by",
            "outward": "blocks",
        },
        {
            "id": "10001",
            "name": "Relates",
            "inward": "relates to",
            "outward": "relates to",
        },
    ]
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


class TestIssueLinks:
    """Tests for sync IssueLinks API."""

    def test_get_link_types(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_LINK_TYPES_RESPONSE)

        api = IssueLinks(_make_sync_client(test_credentials, handler))
        result = api.get_link_types()

        assert len(result["issueLinkTypes"]) == 2
        assert result["issueLinkTypes"][0]["name"] == "Blocks"

    def test_create_link(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            # Jira returns 201 Created with no response body
            return httpx.Response(201)

        api = IssueLinks(_make_sync_client(test_credentials, handler))
        result = api.create_link("Blocks", "TEST-2", "TEST-1")

        assert result is None

    def test_delete_link(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        api = IssueLinks(_make_sync_client(test_credentials, handler))
        result = api.delete_link("10100")

        assert result is None


class TestIssueLinksAsync:
    """Tests for async IssueLinks API."""

    @pytest.mark.asyncio
    async def test_get_link_types(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_LINK_TYPES_RESPONSE)

        api = IssueLinksAsync(_make_async_client(test_credentials, handler))
        result = await api.get_link_types()

        assert len(result["issueLinkTypes"]) == 2

    @pytest.mark.asyncio
    async def test_create_link(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201)

        api = IssueLinksAsync(_make_async_client(test_credentials, handler))
        result = await api.create_link("Blocks", "TEST-2", "TEST-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_link(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        api = IssueLinksAsync(_make_async_client(test_credentials, handler))
        result = await api.delete_link("10100")

        assert result is None
