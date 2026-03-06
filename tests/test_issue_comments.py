"""Tests for IssueComments API."""

import httpx
import pytest

from jira2py.api.issue_comments import IssueComments, IssueCommentsAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_COMMENTS_RESPONSE = {
    "startAt": 0,
    "maxResults": 100,
    "total": 1,
    "comments": [
        {
            "id": "10000",
            "body": {"type": "doc", "content": []},
            "author": {"displayName": "John Doe"},
        }
    ],
}

SAMPLE_ADD_COMMENT_RESPONSE = {
    "id": "10001",
    "body": {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Test comment"}]}
        ],
    },
    "author": {"displayName": "John Doe"},
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


class TestIssueComments:
    """Tests for sync IssueComments API."""

    def test_get_comments(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_COMMENTS_RESPONSE)

        api = IssueComments(_make_sync_client(test_credentials, handler))
        result = api.get_comments("TEST-1")

        assert result["total"] == 1
        assert result["comments"][0]["id"] == "10000"

    def test_add_comment(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_ADD_COMMENT_RESPONSE)

        api = IssueComments(_make_sync_client(test_credentials, handler))
        body = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test comment"}],
                }
            ],
        }
        result = api.add_comment("TEST-1", body=body)

        assert result["id"] == "10001"


class TestIssueCommentsAsync:
    """Tests for async IssueComments API."""

    @pytest.mark.asyncio
    async def test_get_comments(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_COMMENTS_RESPONSE)

        api = IssueCommentsAsync(_make_async_client(test_credentials, handler))
        result = await api.get_comments("TEST-1")

        assert result["total"] == 1
        assert result["comments"][0]["id"] == "10000"
