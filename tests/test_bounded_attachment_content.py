"""Private bounded attachment reads used by managed Markdown image writes."""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest

from jira2py.api.attachments import Attachments
from jira2py.exceptions import JiraConnectionError, JiraError, JiraRateLimitError


class _Body(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.read = False
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        self.read = True
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


def test_bounded_prefix_request_is_authenticated_no_follow_and_range_validated(
    make_client,
) -> None:
    payload = b"p" * 64

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/api/3/attachment/content/10000"
        assert request.url.params["redirect"] == "false"
        assert request.headers["accept"] == "*/*"
        assert request.headers["accept-encoding"] == "identity"
        assert request.headers["range"] == "bytes=0-63"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(
            206,
            headers={
                "Content-Range": " Bytes 0-63/128 ",
                "Content-Length": "64",
                "Content-Encoding": "identity",
            },
            stream=httpx.ByteStream(payload),
        )

    api = Attachments(make_client(handler))
    content = api._get_attachment_content_bounded(
        "10000", expected_size=128, max_bytes=100 * 1024 * 1024, byte_range=(0, 63)
    )

    assert not content.complete
    assert content.body.read() == payload
    content.body.close()


def test_bounded_prefix_accepts_complete_200_without_a_second_request(
    make_client,
) -> None:
    payload = b"x" * 64
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200, headers={"Content-Length": "64"}, stream=httpx.ByteStream(payload)
        )

    api = Attachments(make_client(handler))
    content = api._get_attachment_content_bounded(
        "10000", expected_size=64, max_bytes=64, byte_range=(0, 63)
    )

    assert content.complete
    assert content.body.read() == payload
    assert calls == 1
    content.body.close()


def test_bounded_full_read_requires_an_exact_complete_response(make_client) -> None:
    payload = b"full-content"

    def handler(request: httpx.Request) -> httpx.Response:
        assert "range" not in request.headers
        return httpx.Response(
            200,
            headers={"Content-Length": str(len(payload))},
            stream=httpx.ByteStream(payload),
        )

    api = Attachments(make_client(handler))
    content = api._get_attachment_content_bounded(
        "10000", expected_size=len(payload), max_bytes=len(payload)
    )

    assert content.complete
    assert content.body.read() == payload
    content.body.close()


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Range": "bytes 1-64/128"},
        {"Content-Range": "bytes 0-63/*"},
        {"Content-Range": "bytes 0-63/127"},
        {"Content-Range": "bytes 0-63/128", "Content-Encoding": "gzip"},
        {"Content-Range": "bytes 0-63/128", "Content-Length": "63"},
    ],
)
def test_bounded_prefix_rejects_invalid_headers_without_reading_body(
    make_client, headers: dict[str, str]
) -> None:
    body = _Body([b"sensitive attachment bytes"])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(206, headers=headers, stream=body)

    api = Attachments(make_client(handler))
    with pytest.raises(JiraError, match="response failed validation"):
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    assert not body.read
    assert body.closed


@pytest.mark.parametrize("chunks", [[b"short"], [b"x" * 65]])
def test_bounded_prefix_rejects_truncated_or_overlong_streams(
    make_client, chunks: list[bytes]
) -> None:
    body = _Body(chunks)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            206,
            headers={"Content-Range": "bytes 0-63/128"},
            stream=body,
        )

    api = Attachments(make_client(handler))
    with pytest.raises(JiraError, match="response failed validation"):
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    assert body.read
    assert body.closed


def test_bounded_stream_read_error_is_a_connection_failure_without_retry(
    make_client,
) -> None:
    calls = 0

    class _PartialBody(httpx.SyncByteStream):
        def __init__(self) -> None:
            self.closed = False

        def __iter__(self) -> Iterator[bytes]:
            yield b"partial"
            raise httpx.ReadError("stream interrupted")

        def close(self) -> None:
            self.closed = True

    body = _PartialBody()

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            206,
            headers={"Content-Range": "bytes 0-63/128", "Content-Length": "64"},
            stream=body,
        )

    api = Attachments(make_client(handler))
    with pytest.raises(JiraConnectionError, match="Network error"):
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    assert calls == 1
    assert body.closed


def test_bounded_read_rejects_redirect_without_reading_a_signed_body(
    make_client,
) -> None:
    body = _Body([b"signed attachment body"])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            303,
            headers={"Location": "https://media.example/signed-secret"},
            stream=body,
        )

    api = Attachments(make_client(handler))
    with pytest.raises(JiraError, match="response failed validation"):
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    assert not body.read
    assert body.closed


def test_bounded_integrity_failure_redacts_request_and_body_from_tracebacks(
    make_client,
) -> None:
    secret = "response-body-secret"
    body = _Body([secret.encode() * 8])

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(
            206,
            headers={"Content-Range": "bytes 0-63/128"},
            stream=body,
        )

    api = Attachments(make_client(handler))
    with pytest.raises(JiraError) as exc_info:
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    pending: list[BaseException] = [exc_info.value]
    seen: set[int] = set()
    while pending:
        error = pending.pop()
        if id(error) in seen:
            continue
        seen.add(id(error))
        assert secret not in str(error)
        assert secret not in repr(error)
        traceback = error.__traceback__
        while traceback is not None:
            if "/src/jira2py/" in traceback.tb_frame.f_code.co_filename:
                for value in traceback.tb_frame.f_locals.values():
                    assert not isinstance(value, (httpx.Request, httpx.Response))
                    assert secret not in repr(value)
            traceback = traceback.tb_next
        if error.__context__ is not None:
            pending.append(error.__context__)
        if error.__cause__ is not None:
            pending.append(error.__cause__)

    assert body.closed


def test_bounded_read_retries_only_rate_limits_without_reading_bodies(
    make_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    bodies: list[_Body] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        body = _Body([b"rate-limited body"])
        bodies.append(body)
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, stream=body)
        return httpx.Response(
            200, headers={"Content-Length": "4"}, stream=httpx.ByteStream(b"done")
        )

    monkeypatch.setattr("tenacity.nap.time.sleep", lambda _delay: None)
    api = Attachments(make_client(handler))
    api._client._max_retries = 1
    content = api._get_attachment_content_bounded(
        "10000", expected_size=4, max_bytes=4, byte_range=(0, 3)
    )

    assert content.complete
    assert content.body.read() == b"done"
    assert calls == 2
    assert bodies[0].closed and not bodies[0].read
    content.body.close()


def test_bounded_rate_limit_failure_has_no_response_or_body(make_client) -> None:
    body = _Body([b"sensitive rate-limit body"])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"}, stream=body)

    api = Attachments(make_client(handler))
    api._client._max_retries = 0
    with pytest.raises(JiraRateLimitError) as exc_info:
        api._get_attachment_content_bounded(
            "10000", expected_size=128, max_bytes=128, byte_range=(0, 63)
        )

    assert exc_info.value.response is None
    assert exc_info.value.error_messages == []
    assert body.closed and not body.read
