"""Tests for Attachments API."""

import httpx
import pytest

from jira2py.api.attachments import Attachments, AttachmentsAsync
from jira2py.client import JiraClientAsync, JiraClientSync

SAMPLE_ATTACHMENT = {
    "id": "10001",
    "filename": "report.pdf",
    "mimeType": "application/pdf",
    "size": 12345,
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


class TestAttachments:
    """Tests for sync Attachments API."""

    def test_get_attachment_metadata(self, test_credentials):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ATTACHMENT)

        api = Attachments(_make_sync_client(test_credentials, handler))
        result = api.get_attachment_metadata("10001")

        assert result["id"] == "10001"
        assert result["filename"] == "report.pdf"


class TestAttachmentsAsync:
    """Tests for async Attachments API."""

    @pytest.mark.asyncio
    async def test_get_attachment_metadata(self, test_credentials):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ATTACHMENT)

        api = AttachmentsAsync(_make_async_client(test_credentials, handler))
        result = await api.get_attachment_metadata("10001")

        assert result["id"] == "10001"
        assert result["filename"] == "report.pdf"
