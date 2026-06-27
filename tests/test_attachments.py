"""Tests for Attachments API."""

import httpx

from jira2py.api.attachments import Attachments

SAMPLE_ATTACHMENT = {
    "id": "10000",
    "filename": "screenshot.png",
    "size": 12345,
    "mimeType": "image/png",
    "content": "https://cdn.example.test/10000",
}

SAMPLE_ISSUE_ATTACHMENTS = {
    "key": "TEST-1",
    "fields": {"attachment": [SAMPLE_ATTACHMENT]},
}


class TestAttachments:
    """Tests for Attachments API."""

    def test_get_issue_attachments(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1"
            assert request.url.params["fields"] == "attachment"
            return httpx.Response(200, json=SAMPLE_ISSUE_ATTACHMENTS)

        api = Attachments(make_client(handler))
        result = api.get_issue_attachments("TEST-1")

        assert result == [SAMPLE_ATTACHMENT]

    def test_get_attachment_metadata(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/attachment/10000"
            return httpx.Response(200, json=SAMPLE_ATTACHMENT)

        api = Attachments(make_client(handler))
        result = api.get_attachment_metadata("10000")

        assert result["filename"] == "screenshot.png"
        assert result["size"] == 12345

    def test_download_attachment_content(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/attachment/content/10000"
            return httpx.Response(200, content=b"hello world")

        api = Attachments(make_client(handler))
        result = api.download_attachment_content("10000")

        assert result == b"hello world"

    def test_add_attachment_uses_jira_cloud_multipart_upload(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/rest/api/3/issue/TEST-1/attachments"
            assert request.headers["x-atlassian-token"] == "no-check"
            assert "multipart/form-data" in request.headers["content-type"]
            assert b'filename="sample.txt"' in request.content
            assert b"hello world" in request.content
            return httpx.Response(200, json=[SAMPLE_ATTACHMENT])

        api = Attachments(make_client(handler))
        result = api.add_attachment(
            "TEST-1",
            filename="sample.txt",
            content=b"hello world",
            content_type="text/plain",
        )

        assert result == [SAMPLE_ATTACHMENT]

    def test_delete_attachment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert request.url.path == "/rest/api/3/attachment/10000"
            return httpx.Response(204)

        api = Attachments(make_client(handler))

        assert api.delete_attachment("10000") is None
