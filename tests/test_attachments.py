"""Tests for Attachments API."""

import httpx

from jira2py.api.attachments import Attachments

SAMPLE_ATTACHMENT = {
    "id": "10000",
    "filename": "screenshot.png",
    "size": 12345,
    "mimeType": "image/png",
}


class TestAttachments:
    """Tests for Attachments API."""

    def test_get_attachment_metadata(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_ATTACHMENT)

        api = Attachments(make_client(handler))
        result = api.get_attachment_metadata("10000")

        assert result["filename"] == "screenshot.png"
        assert result["size"] == 12345
