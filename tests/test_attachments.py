"""Tests for Attachments API."""

import httpx
import pytest

from jira2py.api.attachments import Attachments
from jira2py.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)

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
_REJECTED_LOCATION = (
    "https://api.media.atlassian.com/file/unsafe-media-uuid/binary?"
    "token=signed-query-secret&Authorization=redirect-auth-secret"
    "&Cookie=redirect-cookie-secret"
)
_FORBIDDEN_REDIRECT_VALUES = (
    _REJECTED_LOCATION,
    "signed-query-secret",
    "unsafe-media-uuid",
    "redirect-auth-secret",
    "redirect-cookie-secret",
    "request-cookie-secret",
    "Basic ",
)


def _assert_rejected_redirect_is_redacted(error: BaseException) -> None:
    """Check every exception graph traceback without traversing unrelated state."""
    pending = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        assert current.__cause__ is None
        assert current.__context__ is None
        assert getattr(current, "response", None) is None
        assert all(secret not in str(current) for secret in _FORBIDDEN_REDIRECT_VALUES)
        assert all(secret not in repr(current) for secret in _FORBIDDEN_REDIRECT_VALUES)

        traceback = current.__traceback__
        while traceback is not None:
            for value in traceback.tb_frame.f_locals.values():
                assert not isinstance(value, (httpx.Request, httpx.Response))
                assert all(
                    secret not in repr(value) for secret in _FORBIDDEN_REDIRECT_VALUES
                )
            traceback = traceback.tb_next

        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


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

    def test_managed_media_redirect_is_headers_only_and_never_followed(
        self, make_client
    ):
        signed_location = (
            "https://api.media.atlassian.com/file/"
            "123e4567-e89b-12d3-a456-426614174000/binary?token=secret"
        )
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            assert request.url.path == "/rest/api/3/attachment/content/10000"
            assert request.headers["authorization"].startswith("Basic ")
            return httpx.Response(303, headers={"Location": signed_location})

        api = Attachments(make_client(handler))

        assert api._get_attachment_content_redirect_location("10000") == signed_location
        assert len(requests) == 1

    def test_managed_media_requires_one_redirect_location(self, make_client):
        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"attachment bytes"

            def close(self) -> None:
                self.closed = True

        body = Body()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"].startswith("Basic ")
            assert request.headers["cookie"] == "request-cookie-secret"
            return httpx.Response(
                303,
                headers=[
                    ("Location", _REJECTED_LOCATION),
                    ("Location", f"{_REJECTED_LOCATION}&other=1"),
                ],
                stream=body,
            )

        api = Attachments(make_client(handler))
        api._client._get_persistent_client().headers["Cookie"] = "request-cookie-secret"

        with pytest.raises(JiraError) as exc_info:
            api._get_attachment_content_redirect_location("10000")

        assert "Location header" in str(exc_info.value)
        assert not body.read
        assert body.closed
        _assert_rejected_redirect_is_redacted(exc_info.value)

    def test_managed_media_requires_a_redirect_location(self, make_client):
        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"attachment bytes"

            def close(self) -> None:
                self.closed = True

        body = Body()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"].startswith("Basic ")
            assert request.headers["cookie"] == "request-cookie-secret"
            return httpx.Response(303, stream=body)

        api = Attachments(make_client(handler))
        api._client._get_persistent_client().headers["Cookie"] = "request-cookie-secret"

        with pytest.raises(JiraError, match="Location header") as exc_info:
            api._get_attachment_content_redirect_location("10000")

        assert not body.read
        assert body.closed
        _assert_rejected_redirect_is_redacted(exc_info.value)

    def test_managed_media_rejects_non_303_without_reading_a_body(self, make_client):
        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"attachment bytes"

            def close(self) -> None:
                self.closed = True

        body = Body()

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, stream=body)

        api = Attachments(make_client(handler))

        with pytest.raises(JiraError, match="HTTP 303"):
            api._get_attachment_content_redirect_location("10000")

        assert not body.read
        assert body.closed

    @pytest.mark.parametrize(
        ("status_code", "error_type"),
        [
            (400, JiraValidationError),
            (401, JiraAuthenticationError),
            (403, JiraAuthenticationError),
            (404, JiraNotFoundError),
            (429, JiraRateLimitError),
            (422, JiraAPIError),
            (500, JiraAPIError),
        ],
    )
    def test_managed_media_error_responses_are_headers_only(
        self, make_client, status_code, error_type
    ):
        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"sensitive error body"

            def close(self) -> None:
                self.closed = True

        body = Body()

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"].startswith("Basic ")
            assert request.headers["cookie"] == "request-cookie-secret"
            return httpx.Response(
                status_code,
                headers={"Location": _REJECTED_LOCATION, "Retry-After": "7"},
                stream=body,
            )

        api = Attachments(make_client(handler))
        api._client._get_persistent_client().headers["Cookie"] = "request-cookie-secret"
        api._client._max_retries = 0

        with pytest.raises(error_type) as exc_info:
            api._get_attachment_content_redirect_location("10000")

        assert exc_info.value.status_code == status_code
        assert exc_info.value.response is None
        assert exc_info.value.error_messages == []
        if status_code == 429:
            assert exc_info.value.retry_after == 7.0
        assert not body.read
        assert body.closed
        _assert_rejected_redirect_is_redacted(exc_info.value)

    def test_managed_media_retries_429_without_retaining_response(self, make_client):
        calls = 0

        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"attachment bytes"

            def close(self) -> None:
                self.closed = True

        bodies: list[Body] = []

        def handler(_request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            body = Body()
            bodies.append(body)
            if calls < 3:
                return httpx.Response(
                    429,
                    headers={"Location": _REJECTED_LOCATION, "Retry-After": "0"},
                    stream=body,
                )
            return httpx.Response(
                303,
                headers={"Location": "https://api.media.atlassian.com/file/ok/binary"},
                stream=body,
            )

        api = Attachments(make_client(handler))

        assert (
            api._get_attachment_content_redirect_location("10000")
            == "https://api.media.atlassian.com/file/ok/binary"
        )
        assert calls == 3
        assert all(not body.read and body.closed for body in bodies)

    @pytest.mark.parametrize("retry_after", ["-1", "NaN", "Infinity", "not-a-number"])
    def test_managed_media_invalid_retry_after_uses_configured_retry_wait(
        self, make_client, monkeypatch, retry_after
    ):
        class Body(httpx.SyncByteStream):
            def __init__(self) -> None:
                self.read = False
                self.closed = False

            def __iter__(self):
                self.read = True
                yield b"rate limit body"

            def close(self) -> None:
                self.closed = True

        calls = 0
        bodies: list[Body] = []
        sleeps: list[float] = []

        def handler(_request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            body = Body()
            bodies.append(body)
            return httpx.Response(
                429,
                headers={"Retry-After": retry_after},
                stream=body,
            )

        monkeypatch.setattr(
            "jira2py.client.client_sync.random.uniform", lambda *_args: 1.0
        )
        monkeypatch.setattr("tenacity.nap.time.sleep", sleeps.append)
        api = Attachments(make_client(handler))
        api._client._max_retries = 2

        with pytest.raises(JiraRateLimitError) as exc_info:
            api._get_attachment_content_redirect_location("10000")

        assert exc_info.value.retry_after is None
        assert calls == 3
        assert sleeps == [5.0, 10.0]
        assert all(not body.read and body.closed for body in bodies)

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
