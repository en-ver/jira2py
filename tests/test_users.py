"""Tests for Users API."""

import httpx
import pytest

from jira2py.api.users import Users, UsersAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_USERS_RESPONSE = [
    {
        "accountId": "user1",
        "displayName": "John Doe",
        "emailAddress": "john@example.com",
    },
    {
        "accountId": "user2",
        "displayName": "Jane Smith",
        "emailAddress": "jane@example.com",
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


class TestUsers:
    """Tests for sync Users API."""

    def test_search_users(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_USERS_RESPONSE)

        api = Users(_make_sync_client(test_credentials, handler))
        result = api.search_users(query="john")

        assert len(result) == 2
        assert result[0]["displayName"] == "John Doe"

    def test_search_users_with_pagination(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_USERS_RESPONSE[:1])

        api = Users(_make_sync_client(test_credentials, handler))
        result = api.search_users(query="john", start_at=0, max_results=1)

        assert len(result) == 1


class TestUsersAsync:
    """Tests for async Users API."""

    @pytest.mark.asyncio
    async def test_search_users(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_USERS_RESPONSE)

        api = UsersAsync(_make_async_client(test_credentials, handler))
        result = await api.search_users(query="john")

        assert len(result) == 2
        assert result[0]["displayName"] == "John Doe"
