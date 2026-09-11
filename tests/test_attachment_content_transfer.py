"""Public bounded streaming attachment transfer tests."""

from __future__ import annotations

import io
from collections.abc import Iterator
from typing import BinaryIO, cast

import httpx
import pytest

from jira2py.api.attachments import Attachments
from jira2py.exceptions import JiraConnectionError, JiraError, JiraRateLimitError


class _Chunks(httpx.SyncByteStream):
    def __init__(self, chunks: list[bytes], error: Exception | None = None) -> None:
        self.chunks = chunks
        self.error = error
        self.read = False
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        self.read = True
        yield from self.chunks
        if self.error is not None:
            raise self.error

    def close(self) -> None:
        self.closed = True


def test_transfer_streams_multiple_chunks_and_returns_observed_bytes(
    make_client,
) -> None:
    body = _Chunks([b"hello ", b"world"])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=body)

    destination = io.BytesIO()
    observed = Attachments(make_client(handler)).download_attachment_content(
        "10000", destination, max_bytes=11, expected_size=11
    )

    assert observed == 11
    assert destination.getvalue() == b"hello world"
    assert body.closed


@pytest.mark.parametrize(
    ("max_bytes", "expected_size", "error"),
    [
        (False, None, TypeError),
        (0, None, ValueError),
        (1, False, TypeError),
        (1, -1, ValueError),
        (1, 2, ValueError),
    ],
)
def test_transfer_validates_bounds_before_request(
    make_client, max_bytes: object, expected_size: object, error: type[Exception]
) -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200)

    with pytest.raises(error):
        Attachments(make_client(handler)).download_attachment_content(
            "10000",
            io.BytesIO(),
            max_bytes=cast(int, max_bytes),
            expected_size=cast(int | None, expected_size),
        )

    assert calls == 0


def test_transfer_enforces_cumulative_limit_before_writing_offending_chunk(
    make_client,
) -> None:
    first_chunk = b"a" * (64 * 1024)
    body = _Chunks([first_chunk, b"b"])
    destination = io.BytesIO()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=body)

    with pytest.raises(JiraError, match="failed validation"):
        Attachments(make_client(handler)).download_attachment_content(
            "10000", destination, max_bytes=len(first_chunk)
        )

    assert destination.getvalue() == first_chunk
    assert body.closed


@pytest.mark.parametrize(
    ("content", "expected_size", "passes"),
    [
        (b"hello", None, True),
        (b"hello", 5, True),
        (b"hell", 5, False),
        (b"hello!", 5, False),
        (b"", 0, True),
        (b"x", 0, False),
    ],
)
def test_transfer_enforces_optional_expected_size(
    make_client, content: bytes, expected_size: int | None, passes: bool
) -> None:
    destination = io.BytesIO()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=_Chunks([content]))

    transfer = Attachments(make_client(handler)).download_attachment_content
    if passes:
        assert transfer(
            "10000",
            destination,
            max_bytes=10,
            expected_size=expected_size,
        ) == len(content)
    else:
        with pytest.raises(JiraError, match="failed validation"):
            transfer("10000", destination, max_bytes=10, expected_size=expected_size)


class _ShortDestination:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def write(self, value: bytes) -> int:
        self.parts.append(value[:1])
        return 1


class _FailingDestination:
    def write(self, _value: bytes) -> int:
        raise OSError("disk full")


def test_transfer_completes_short_writes_and_sanitizes_destination_errors(
    make_client,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"hello")

    short_destination = _ShortDestination()
    observed = Attachments(make_client(handler)).download_attachment_content(
        "10000", cast(BinaryIO, short_destination), max_bytes=5
    )
    assert observed == 5
    assert b"".join(short_destination.parts) == b"hello"

    with pytest.raises(JiraError, match="destination") as exc_info:
        Attachments(make_client(handler)).download_attachment_content(
            "10000", cast(BinaryIO, _FailingDestination()), max_bytes=5
        )
    assert "disk full" not in str(exc_info.value)


def test_transfer_starts_at_jira_endpoint_preserves_parameter_precedence_and_strips_cross_origin_auth(
    make_client,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.host == "test.atlassian.net":
            assert request.url.path == "/rest/api/3/attachment/content/10000"
            assert request.url.params["redirect"] == "false"
            return httpx.Response(
                302,
                headers={"Location": "https://media.example/signed-download"},
                request=request,
            )
        assert request.url.host == "media.example"
        assert "authorization" not in request.headers
        return httpx.Response(200, content=b"done", request=request)

    destination = io.BytesIO()
    observed = Attachments(make_client(handler)).download_attachment_content(
        "10000",
        destination,
        max_bytes=4,
        redirect=True,
        extra_params={"redirect": "false"},
    )

    assert observed == 4
    assert destination.getvalue() == b"done"
    assert len(requests) == 2


def test_transfer_retries_429_before_output_only(make_client, monkeypatch) -> None:
    calls = 0
    rate_limited_body = _Chunks([b"do not read"])

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429, headers={"Retry-After": "0"}, stream=rate_limited_body
            )
        return httpx.Response(200, content=b"done")

    monkeypatch.setattr("tenacity.nap.time.sleep", lambda _delay: None)
    api = Attachments(make_client(handler))
    api._client._max_retries = 1
    destination = io.BytesIO()

    assert api.download_attachment_content("10000", destination, max_bytes=4) == 4
    assert calls == 2
    assert rate_limited_body.closed and not rate_limited_body.read


def test_transfer_does_not_retry_after_partial_stream_failure(make_client) -> None:
    calls = 0
    partial = b"p" * (64 * 1024)
    body = _Chunks([partial], httpx.ReadError("stream stopped"))

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, stream=body)

    api = Attachments(make_client(handler))
    api._client._max_retries = 3
    destination = io.BytesIO()

    with pytest.raises(JiraConnectionError, match="Network error"):
        api.download_attachment_content(
            "10000", destination, max_bytes=len(partial) + 1
        )

    assert calls == 1
    assert destination.getvalue() == partial


def test_transfer_status_errors_do_not_read_error_body_or_retain_response(
    make_client,
) -> None:
    body = _Chunks([b"sensitive error body"])

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"}, stream=body)

    api = Attachments(make_client(handler))
    api._client._max_retries = 0

    with pytest.raises(JiraRateLimitError) as exc_info:
        api.download_attachment_content("10000", io.BytesIO(), max_bytes=10)

    assert exc_info.value.response is None
    assert exc_info.value.error_messages == []
    assert body.closed and not body.read
