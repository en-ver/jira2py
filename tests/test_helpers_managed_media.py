from __future__ import annotations

import io
from copy import deepcopy
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import httpx
import pytest
from adf_bridge import ResolvedJiraImage

from jira2py import JiraAPI
from jira2py.api.attachments import Attachments
from jira2py.client.client_sync import _BoundedJiraContent
from jira2py.exceptions import JiraConnectionError
from jira2py.helpers._adf import markdown_to_adf
from jira2py.helpers._managed_media import (
    _classify_attachment_content_url,
    _configured_jira_origin,
    _JiraMarkdownWriteSession,
    _media_id_from_redirect_location,
)
from jira2py.helpers.attachments import DEFAULT_MAX_DOWNLOAD
from jira2py.helpers.comments import CommentHelpers
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError
from jira2py.helpers.issues import IssueHelpers
from jira2py.helpers.worklogs import WorklogHelpers

_MEDIA_ID = "123e4567-e89b-12d3-a456-426614174000"
_CONTENT_URL = "https://example.atlassian.net/rest/api/3/attachment/content/10000"
_MEDIA_LOCATION = (
    f"https://api.media.atlassian.com/file/{_MEDIA_ID}/binary?token=secret"
)


def _rejected_signed_location() -> str:
    return (
        "https://api.media.atlassian.com/file/unsafe-media-uuid/binary?"
        "token=signed-query-secret&Authorization=redirect-auth-secret"
        "&Cookie=redirect-cookie-secret"
    )


def _assert_rejected_redirect_traceback_is_redacted(error: BaseException) -> None:
    forbidden = (
        "https://api.media.atlassian.com/file/unsafe-media-uuid/binary?"
        "token=signed-query-secret&Authorization=redirect-auth-secret"
        "&Cookie=redirect-cookie-secret",
        "signed-query-secret",
        "Authorization",
        "Cookie",
        "unsafe-media-uuid",
    )
    for value in forbidden:
        assert value not in str(error)
        assert value not in repr(error)
        assert value not in repr(getattr(error, "details", {}))

    traceback = error.__traceback__
    while traceback is not None:
        for value in traceback.tb_frame.f_locals.values():
            assert all(secret not in repr(value) for secret in forbidden)
        traceback = traceback.tb_next


def _assert_transport_failure_graph_is_redacted(error: BaseException) -> None:
    """Follow chained errors and retry outcomes reachable from library tracebacks."""
    forbidden = ("Basic ", "request-cookie-secret", "request-extra-secret")
    pending = [error]
    seen: set[int] = set()

    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        assert not isinstance(current, httpx.HTTPError)
        assert all(secret not in str(current) for secret in forbidden)
        assert all(secret not in repr(current) for secret in forbidden)

        traceback = current.__traceback__
        while traceback is not None:
            frame = traceback.tb_frame
            if "/src/jira2py/" in frame.f_code.co_filename:
                for value in frame.f_locals.values():
                    assert not isinstance(value, (httpx.Request, httpx.Response))
                    assert all(secret not in repr(value) for secret in forbidden)
                    retry_state = getattr(value, "retry_state", None)
                    outcome = getattr(retry_state, "outcome", None)
                    if outcome is not None:
                        outcome_error = outcome.exception()
                        if outcome_error is not None:
                            pending.append(outcome_error)
            traceback = traceback.tb_next

        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


def _assert_exception_graph_and_traceback_locals_are_redacted(
    error: BaseException, *forbidden: str
) -> None:
    pending = [error]
    seen: set[int] = set()

    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))

        assert all(value not in str(current) for value in forbidden)
        assert all(value not in repr(current) for value in forbidden)

        traceback = current.__traceback__
        while traceback is not None:
            frame = traceback.tb_frame
            if "/src/jira2py/" in frame.f_code.co_filename:
                for value in frame.f_locals.values():
                    assert not isinstance(value, (httpx.Request, httpx.Response))
                    assert all(item not in repr(value) for item in forbidden)
            traceback = traceback.tb_next

        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


def _png_prefix(width: int = 32, height: int = 48) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00" * 35
    )


def _bounded_png_prefix() -> _BoundedJiraContent:
    return _BoundedJiraContent(io.BytesIO(_png_prefix()), complete=False)


def _make_api() -> SimpleNamespace:
    attachments = Mock()
    attachments._get_attachment_content_bounded.side_effect = (
        lambda *_args, **_kwargs: _bounded_png_prefix()
    )
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        attachments=attachments,
        comments=Mock(),
        fields=Mock(),
        issues=Mock(),
        worklogs=Mock(),
    )


def _attachment(
    attachment_id: str = "10000", mime_type: str = "image/png"
) -> dict[str, Any]:
    return {
        "id": attachment_id,
        "mimeType": mime_type,
        "filename": "screen.png",
        "size": 256,
    }


def test_only_canonical_configured_attachment_urls_are_managed() -> None:
    origin = _configured_jira_origin("https://example.atlassian.net")
    assert _classify_attachment_content_url(_CONTENT_URL, origin) == (
        "candidate",
        "10000",
    )
    assert _classify_attachment_content_url(
        "https://example.atlassian.net/rest/api/3/attachment/content/010",
        origin,
    ) == ("malformed", None)
    assert _classify_attachment_content_url(f"{_CONTENT_URL}?download=1", origin) == (
        "malformed",
        None,
    )
    assert _classify_attachment_content_url(f"{_CONTENT_URL}?", origin) == (
        "malformed",
        None,
    )
    assert _classify_attachment_content_url(f"{_CONTENT_URL}#", origin) == (
        "malformed",
        None,
    )
    assert _classify_attachment_content_url(f"{_CONTENT_URL}#fragment", origin) == (
        "malformed",
        None,
    )
    assert _classify_attachment_content_url(
        "https://example.atlassian.net/secure/attachment/10000", origin
    ) == ("external", None)
    assert _classify_attachment_content_url(
        "/rest/api/3/attachment/content/10000", origin
    ) == (
        "external",
        None,
    )
    assert _classify_attachment_content_url(
        "https://elsewhere.example/rest/api/3/attachment/content/10000", origin
    ) == ("external", None)
    assert _configured_jira_origin("https://example.atlassian.net:0") is None
    assert _configured_jira_origin("https://example.atlassian.net:invalid") is None
    assert _classify_attachment_content_url(
        "https://example.atlassian.net:0/rest/api/3/attachment/content/10000", origin
    ) == ("external", None)
    assert _classify_attachment_content_url(
        "https://example.atlassian.net:invalid/rest/api/3/attachment/content/10000",
        origin,
    ) == ("malformed", None)


def test_issue_edit_resolves_repeated_images_once_and_reads_back_all_fields() -> None:
    api = _make_api()
    api.fields.get_fields.return_value = []
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )
    captured: dict[str, Any] = {}

    def edit_issue(**kwargs: Any) -> dict[str, str]:
        captured.update(kwargs)
        return {"key": "PROJ-1"}

    api.issues.edit_issue.side_effect = edit_issue
    api.issues.get_issue.side_effect = lambda **_kwargs: {
        "fields": {
            "environment": captured["fields"]["environment"],
            "description": captured["fields"]["description"],
        },
    }

    result = IssueHelpers(cast(JiraAPI, api)).edit(
        "PROJ-1",
        description=f'![one]({_CONTENT_URL} "ignored title") and ![again]({_CONTENT_URL})',
        fields={"environment": f"![environment]({_CONTENT_URL})"},
        raw=True,
    )

    api.attachments.get_issue_attachments.assert_called_once_with("PROJ-1")
    api.attachments._get_attachment_content_redirect_location.assert_called_once_with(
        "10000"
    )
    api.issues.get_issue.assert_called_once_with(
        issue_id="PROJ-1",
        fields=["environment", "description"],
    )
    assert result.data == {"key": "PROJ-1"}
    content = captured["fields"]["description"]["content"]
    media = [
        block["content"][0]["attrs"]
        for block in content
        if block["type"] == "mediaSingle"
    ]
    assert [attrs["id"] for attrs in media] == [_MEDIA_ID, _MEDIA_ID]
    assert set(media[0]) == {"type", "id", "collection", "alt", "width", "height"}
    assert media[0]["width"] == 32
    assert media[0]["height"] == 48
    assert media[1]["alt"] == "again"
    assert (
        captured["fields"]["environment"]["content"][0]["content"][0]["attrs"][
            "collection"
        ]
        == ""
    )
    assert captured["fields"]["description"]["content"][0]["attrs"] == {
        "layout": "center",
        "width": 100,
        "widthType": "percentage",
    }


def test_managed_images_in_root_and_lists_are_dimensioned_once_per_attachment() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )

    prepared = _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
        f"![root]({_CONTENT_URL})\n\n- ![list]({_CONTENT_URL})"
    )

    document = cast(Any, prepared.document)
    root_media = document["content"][0]
    list_media = document["content"][1]["content"][0]["content"][0]
    for media_single in (root_media, list_media):
        assert media_single["type"] == "mediaSingle"
        assert media_single["attrs"] == {
            "layout": "center",
            "width": 100,
            "widthType": "percentage",
        }
        assert media_single["content"][0]["attrs"]["width"] == 32
        assert media_single["content"][0]["attrs"]["height"] == 48
    api.attachments._get_attachment_content_bounded.assert_called_once()
    api.attachments._get_attachment_content_redirect_location.assert_called_once()


def test_managed_jpeg_uses_one_full_fallback_after_the_prefix_probe(
    make_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    jpeg = (
        b"\xff\xd8\xff\xfe\x00\x42"
        + b"x" * 64
        + b"\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03"
        b"\x01\x11\x00\x02\x11\x00\x03\x11\x00\xff\xd9"
    )
    content_ranges: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/api/3/issue/PROJ-1":
            return httpx.Response(
                200,
                json={
                    "fields": {
                        "attachment": [
                            {
                                **_attachment(),
                                "mimeType": "image/jpeg",
                                "size": len(jpeg),
                            }
                        ]
                    }
                },
            )

        assert request.url.path == "/rest/api/3/attachment/content/10000"
        assert request.url.params["redirect"] == "false"
        assert request.headers["accept"] == "*/*"
        assert request.headers["accept-encoding"] == "identity"
        content_ranges.append(request.headers.get("range"))
        if request.headers.get("range") == "bytes=0-63":
            return httpx.Response(
                206,
                headers={
                    "Content-Range": f"bytes 0-63/{len(jpeg)}",
                    "Content-Length": "64",
                },
                stream=httpx.ByteStream(jpeg[:64]),
            )
        assert "range" not in request.headers
        return httpx.Response(
            200,
            headers={"Content-Length": str(len(jpeg))},
            stream=httpx.ByteStream(jpeg),
        )

    client = make_client(handler)
    attachments = Attachments(client)
    redirect_location = Mock(return_value=_MEDIA_LOCATION)
    monkeypatch.setattr(
        attachments, "_get_attachment_content_redirect_location", redirect_location
    )
    api = SimpleNamespace(
        credentials=client.credentials,
        attachments=attachments,
        issues=Mock(),
    )
    source_url = f"{client.credentials.url}/rest/api/3/attachment/content/10000"

    prepared = _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
        f"![jpeg]({source_url})"
    )

    assert len(jpeg) > 64
    assert prepared.resolved_images[0].width == 640
    assert prepared.resolved_images[0].height == 480
    assert content_ranges == ["bytes=0-63", None]
    redirect_location.assert_called_once_with("10000")


def test_large_fast_path_image_does_not_require_a_full_download() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        {**_attachment(), "size": DEFAULT_MAX_DOWNLOAD + 1}
    ]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )

    prepared = _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
        f"![large]({_CONTENT_URL})"
    )

    assert prepared.resolved_images[0].width == 32
    api.attachments._get_attachment_content_bounded.assert_called_once()
    assert api.attachments._get_attachment_content_bounded.call_args.kwargs[
        "byte_range"
    ] == (
        0,
        63,
    )


def test_unsupported_or_oversized_fallback_requirements_fail_before_write() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        {**_attachment(), "size": DEFAULT_MAX_DOWNLOAD + 1}
    ]
    api.attachments._get_attachment_content_bounded.side_effect = (
        lambda *_args, **_kwargs: _BoundedJiraContent(io.BytesIO(b"unknown"), False)
    )

    with pytest.raises(JiraHelperValidationError, match="complete attachment larger"):
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![unsupported]({_CONTENT_URL})"
        )

    api.attachments._get_attachment_content_bounded.assert_called_once()
    api.attachments._get_attachment_content_redirect_location.assert_not_called()


def test_malformed_or_protocol_invalid_images_fail_before_the_mutation() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_bounded.side_effect = [
        _BoundedJiraContent(io.BytesIO(b"\x89PNG\r\n\x1a\n"), complete=False),
        _BoundedJiraContent(io.BytesIO(b"\x89PNG\r\n\x1a\n"), complete=True),
    ]

    with pytest.raises(JiraHelperValidationError, match="supported managed image"):
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![malformed]({_CONTENT_URL})"
        )

    api.attachments._get_attachment_content_redirect_location.assert_not_called()

    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_bounded.side_effect = (
        lambda *_args, **_kwargs: _BoundedJiraContent(io.BytesIO(b"unknown"), True)
    )
    with pytest.raises(JiraHelperValidationError, match="supported managed image"):
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![complete]({_CONTENT_URL})"
        )

    api.attachments._get_attachment_content_bounded.assert_called_once()
    api.attachments._get_attachment_content_redirect_location.assert_not_called()

    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_bounded.side_effect = RuntimeError(
        "invalid range response"
    )
    with pytest.raises(
        JiraHelperOperationError, match="attachment content"
    ) as exc_info:
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![range]({_CONTENT_URL})"
        )

    assert exc_info.value.details == {}
    api.attachments._get_attachment_content_redirect_location.assert_not_called()


@pytest.mark.parametrize("failure_stage", ["prefix", "fallback"])
def test_managed_bounded_content_failures_have_no_exception_context(
    failure_stage: str,
) -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    original_error = RuntimeError("attachment-content-read-secret")
    if failure_stage == "prefix":
        api.attachments._get_attachment_content_bounded.side_effect = original_error
    else:
        api.attachments._get_attachment_content_bounded.side_effect = [
            _BoundedJiraContent(io.BytesIO(b"unknown"), complete=False),
            original_error,
        ]

    with pytest.raises(
        JiraHelperOperationError, match="attachment content"
    ) as exc_info:
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![screen]({_CONTENT_URL})"
        )

    assert exc_info.value.__cause__ is None
    assert exc_info.value.__context__ is None
    assert exc_info.value.__suppress_context__
    _assert_exception_graph_and_traceback_locals_are_redacted(
        exc_info.value, "attachment-content-read-secret"
    )
    api.attachments._get_attachment_content_redirect_location.assert_not_called()


@pytest.mark.parametrize("size", [None, True, 0, -1])
def test_missing_or_invalid_attachment_size_fails_before_content_read(
    size: Any,
) -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        {**_attachment(), "size": size}
    ]

    with pytest.raises(JiraHelperOperationError, match="size metadata"):
        _JiraMarkdownWriteSession(cast(JiraAPI, api), "PROJ-1").prepare(
            f"![screen]({_CONTENT_URL})"
        )

    api.attachments._get_attachment_content_bounded.assert_not_called()
    api.attachments._get_attachment_content_redirect_location.assert_not_called()


def test_legacy_dimensionless_resolutions_and_external_images_remain_widthless() -> (
    None
):
    legacy = markdown_to_adf(
        f"![legacy]({_CONTENT_URL})",
        resolved_images=[ResolvedJiraImage(_CONTENT_URL, _MEDIA_ID, "")],
    )
    legacy_media = cast(Any, legacy)["content"][0]
    assert legacy_media["attrs"] == {"layout": "center"}
    assert set(legacy_media["content"][0]["attrs"]) == {
        "type",
        "id",
        "collection",
        "alt",
    }

    external = markdown_to_adf("![external](https://images.example/screen.png)")
    assert cast(Any, external)["content"][0]["attrs"] == {"layout": "center"}


def test_external_images_preserve_existing_write_io() -> None:
    api = _make_api()
    api.issues.edit_issue.return_value = None

    IssueHelpers(cast(JiraAPI, api)).edit(
        "PROJ-1", description="![external](https://images.example/screen.png)"
    )

    api.attachments.get_issue_attachments.assert_not_called()
    api.attachments._get_attachment_content_redirect_location.assert_not_called()
    api.issues.get_issue.assert_not_called()
    assert (
        api.issues.edit_issue.call_args.kwargs["fields"]["description"]["content"][0][
            "content"
        ][0]["attrs"]["url"]
        == "https://images.example/screen.png"
    )


def test_raw_adf_and_plain_issue_fields_bypass_managed_image_processing() -> None:
    api = _make_api()
    api.fields.get_fields.return_value = []
    api.issues.edit_issue.return_value = None
    raw_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "raw"}]}
        ],
    }

    IssueHelpers(cast(JiraAPI, api)).edit(
        "PROJ-1", fields={"environment": raw_adf, "labels": ["backend"]}
    )

    assert api.issues.edit_issue.call_args.kwargs["fields"]["environment"] is raw_adf
    api.attachments.get_issue_attachments.assert_not_called()
    api.issues.get_issue.assert_not_called()


@pytest.mark.parametrize(
    "attachment", [_attachment(mime_type="text/plain"), _attachment("10001")]
)
def test_issue_edit_rejects_unassociated_or_non_image_attachments_before_write(
    attachment: dict[str, str],
) -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [attachment]

    with pytest.raises(JiraHelperValidationError, match="associated"):
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({_CONTENT_URL})"
        )

    api.issues.edit_issue.assert_not_called()
    api.attachments._get_attachment_content_redirect_location.assert_not_called()


@pytest.mark.parametrize("url", [_CONTENT_URL, f"{_CONTENT_URL}?download=1"])
def test_issue_create_rejects_managed_or_malformed_attachment_urls_before_post(
    url: str,
) -> None:
    api = _make_api()

    with pytest.raises(JiraHelperValidationError, match="Create the issue first"):
        IssueHelpers(cast(JiraAPI, api)).create(
            "PROJ", "Task", "Summary", description=f"![screen]({url})"
        )

    api.issues.create_issue.assert_not_called()
    api.attachments.get_issue_attachments.assert_not_called()


def test_redirect_validation_rejects_bare_delimiters_and_allows_signed_queries() -> (
    None
):
    assert _media_id_from_redirect_location(_MEDIA_LOCATION) == _MEDIA_ID

    for location in (
        f"https://api.media.atlassian.com:0/file/{_MEDIA_ID}/binary?token=secret",
        f"https://api.media.atlassian.com:invalid/file/{_MEDIA_ID}/binary?token=secret",
        f"https://api.media.atlassian.com/file/{_MEDIA_ID}/binary?",
        f"https://api.media.atlassian.com/file/{_MEDIA_ID}/binary#",
    ):
        with pytest.raises(JiraHelperOperationError, match="approved Media Services"):
            _media_id_from_redirect_location(location)


def test_redirect_validation_redacts_signed_locations_and_media_ids() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        f"https://untrusted.example/file/{_MEDIA_ID}/binary?token=secret"
    )

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({_CONTENT_URL})"
        )

    assert "secret" not in str(exc_info.value)
    assert _MEDIA_ID not in str(exc_info.value)
    api.issues.edit_issue.assert_not_called()


def test_rejected_signed_redirect_traceback_does_not_retain_secrets() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.side_effect = (
        _rejected_signed_location
    )

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({_CONTENT_URL})"
        )

    _assert_rejected_redirect_traceback_is_redacted(exc_info.value)
    api.issues.edit_issue.assert_not_called()


def test_redirect_close_failure_after_signed_location_is_fully_redacted(
    make_client, monkeypatch
) -> None:
    signed_location = (
        f"https://api.media.atlassian.com/file/{_MEDIA_ID}/binary?"
        "token=redirect-close-secret"
    )

    class CloseFailingBody(httpx.SyncByteStream):
        def __init__(self) -> None:
            self.closed = False

        def __iter__(self):
            yield b"unused"

        def close(self) -> None:
            self.closed = True
            raise httpx.ReadError("stream close failed")

    body = CloseFailingBody()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/api/3/issue/PROJ-1":
            return httpx.Response(200, json={"fields": {"attachment": [_attachment()]}})
        assert request.url.path == "/rest/api/3/attachment/content/10000"
        return httpx.Response(303, headers={"Location": signed_location}, stream=body)

    client = make_client(handler)
    attachments = Attachments(client)
    monkeypatch.setattr(
        attachments,
        "_get_attachment_content_bounded",
        Mock(return_value=_bounded_png_prefix()),
    )
    api = SimpleNamespace(
        credentials=client.credentials,
        attachments=attachments,
        issues=Mock(),
    )
    source_url = f"{client.credentials.url}/rest/api/3/attachment/content/10000"

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({source_url})"
        )

    _assert_exception_graph_and_traceback_locals_are_redacted(
        exc_info.value, signed_location, "redirect-close-secret"
    )
    assert body.closed
    api.issues.edit_issue.assert_not_called()


@pytest.mark.parametrize(
    "error_type",
    [httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ConnectError],
)
def test_managed_image_transport_failure_does_not_retain_authenticated_request(
    make_client, error_type
) -> None:
    failed_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/api/3/issue/PROJ-1":
            return httpx.Response(200, json={"fields": {"attachment": [_attachment()]}})
        assert request.url.path == "/rest/api/3/attachment/content/10000"
        assert request.url.params["redirect"] == "false"
        assert request.headers["range"] == "bytes=0-63"
        assert request.headers["accept"] == "*/*"
        assert request.headers["accept-encoding"] == "identity"
        assert request.headers["authorization"].startswith("Basic ")
        assert request.headers["cookie"] == "request-cookie-secret"
        assert request.headers["x-private"] == "request-extra-secret"
        failed_requests.append(request)
        raise error_type("transport failure", request=request)

    client = make_client(handler)
    persistent_client = client._get_persistent_client()
    persistent_client.headers["Cookie"] = "request-cookie-secret"
    persistent_client.headers["X-Private"] = "request-extra-secret"
    api = SimpleNamespace(
        credentials=client.credentials,
        attachments=Attachments(client),
        issues=Mock(),
    )
    source_url = f"{client.credentials.url}/rest/api/3/attachment/content/10000"

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({source_url})"
        )

    _assert_transport_failure_graph_is_redacted(exc_info.value)
    assert len(failed_requests) == 1
    assert not failed_requests[0].headers
    api.issues.edit_issue.assert_not_called()


def test_comment_and_worklog_verify_the_returned_raw_persisted_body() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )

    def comment_response(**kwargs: Any) -> dict[str, Any]:
        return {"id": "10000", "body": kwargs["body"]}

    api.comments.add_comment.side_effect = comment_response
    comment_result = CommentHelpers(cast(JiraAPI, api)).add(
        "PROJ-1", f"![screen]({_CONTENT_URL})"
    )

    api.comments.add_comment.assert_called_once_with(
        issue_id="PROJ-1",
        body=api.comments.add_comment.call_args.kwargs["body"],
    )
    assert comment_result.data == {
        "id": "10000",
        "body": api.comments.add_comment.call_args.kwargs["body"],
    }

    def updated_comment_response(**kwargs: Any) -> dict[str, Any]:
        return {"id": "10000", "body": kwargs["body"]}

    api.comments.update_comment.side_effect = updated_comment_response
    CommentHelpers(cast(JiraAPI, api)).update(
        "PROJ-1", "10000", f"![updated]({_CONTENT_URL})"
    )
    api.comments.update_comment.assert_called_once_with(
        issue_id="PROJ-1",
        comment_id="10000",
        body=api.comments.update_comment.call_args.kwargs["body"],
    )

    def worklog_response(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": "10001",
            "issueId": "10000",
            "author": {"displayName": "Alice", "accountId": "a1"},
            "started": "2026-01-02T10:00:00+0000",
            "timeSpent": "1h",
            "timeSpentSeconds": 3600,
            "comment": kwargs["comment"],
        }

    api.worklogs.add_worklog.side_effect = worklog_response
    worklog_result = WorklogHelpers(cast(JiraAPI, api)).add(
        "PROJ-1", "1h", comment=f"![screen]({_CONTENT_URL})"
    )

    assert worklog_result.data is not None
    assert (
        worklog_result.data["comment"]
        == api.worklogs.add_worklog.call_args.kwargs["comment"]
    )

    api.worklogs.update_worklog.side_effect = worklog_response
    WorklogHelpers(cast(JiraAPI, api)).update(
        "PROJ-1", "10001", comment=f"![updated]({_CONTENT_URL})"
    )
    assert api.attachments.get_issue_attachments.call_count == 4
    assert api.attachments._get_attachment_content_redirect_location.call_count == 4


def test_post_write_verification_failure_is_uncertain_and_never_retried() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )
    api.comments.add_comment.return_value = {"id": "10000", "body": {"type": "doc"}}

    with pytest.raises(
        JiraHelperOperationError,
        match="may have applied.*Reread the comment before retrying",
    ):
        CommentHelpers(cast(JiraAPI, api)).add("PROJ-1", f"![screen]({_CONTENT_URL})")

    api.comments.add_comment.assert_called_once()
    api.attachments.delete_attachment.assert_not_called()


def test_managed_attachment_listing_status_failure_is_fully_sanitized(
    make_client,
) -> None:
    body_secret = "attachment-list-response-body-secret"
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(500, content=body_secret)

    client = make_client(handler)
    api = SimpleNamespace(
        credentials=client.credentials,
        attachments=Attachments(client),
        issues=Mock(),
    )
    source_url = f"{client.credentials.url}/rest/api/3/attachment/content/10000"

    with pytest.raises(JiraHelperOperationError) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit(
            "PROJ-1", description=f"![screen]({source_url})"
        )

    _assert_exception_graph_and_traceback_locals_are_redacted(
        exc_info.value, body_secret, "Basic "
    )
    assert len(requests) == 1
    assert requests[0].headers["authorization"].startswith("Basic ")


@pytest.mark.parametrize("family", ["comment", "issue", "worklog"])
def test_later_preflight_failure_discards_prior_media_resolutions(
    family: str,
) -> None:
    first_media_id = "223e4567-e89b-12d3-a456-426614174000"
    first_location = (
        f"https://api.media.atlassian.com/file/{first_media_id}/binary?token=first"
    )
    second_content_url = _CONTENT_URL.removesuffix("10000") + "10001"
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        _attachment("10000"),
        _attachment("10001"),
    ]

    def redirect_location(attachment_id: str) -> str:
        if attachment_id == "10000":
            return first_location
        return "https://untrusted.example/not-a-media-redirect?token=second"

    api.attachments._get_attachment_content_redirect_location.side_effect = (
        redirect_location
    )

    if family == "comment":

        def invoke() -> None:
            CommentHelpers(cast(JiraAPI, api)).add(
                "PROJ-1",
                f"![first]({_CONTENT_URL}) ![second]({second_content_url})",
            )

        mutation = api.comments.add_comment
    elif family == "issue":

        def invoke() -> None:
            IssueHelpers(cast(JiraAPI, api)).edit(
                "PROJ-1",
                description=f"![first]({_CONTENT_URL}) ![second]({second_content_url})",
            )

        mutation = api.issues.edit_issue
    else:

        def invoke() -> None:
            WorklogHelpers(cast(JiraAPI, api)).add(
                "PROJ-1",
                "1h",
                comment=f"![first]({_CONTENT_URL}) ![second]({second_content_url})",
            )

        mutation = api.worklogs.add_worklog

    with pytest.raises(
        JiraHelperOperationError, match="approved Media Services"
    ) as exc_info:
        invoke()

    _assert_exception_graph_and_traceback_locals_are_redacted(
        exc_info.value, first_media_id
    )
    mutation.assert_not_called()


@pytest.mark.parametrize("later_field", ["description", "custom_textarea"])
def test_issue_edit_rich_fields_are_prepared_transactionally(later_field: str) -> None:
    first_media_id = "223e4567-e89b-12d3-a456-426614174000"
    first_location = (
        f"https://api.media.atlassian.com/file/{first_media_id}/binary?token=first"
    )
    second_content_url = _CONTENT_URL.removesuffix("10000") + "10001"
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        _attachment("10000"),
        _attachment("10001"),
    ]

    def redirect_location(attachment_id: str) -> str:
        if attachment_id == "10000":
            return first_location
        return "https://untrusted.example/not-a-media-redirect?token=second"

    api.attachments._get_attachment_content_redirect_location.side_effect = (
        redirect_location
    )
    fields: dict[str, Any] = {"environment": f"![first]({_CONTENT_URL})"}
    edit_kwargs: dict[str, Any] = {"fields": fields}
    if later_field == "description":
        edit_kwargs["description"] = f"![second]({second_content_url})"
        api.fields.get_fields.return_value = []
    else:
        fields["customfield_10001"] = f"![second]({second_content_url})"
        api.fields.get_fields.return_value = [
            {
                "id": "customfield_10001",
                "schema": {
                    "custom": (
                        "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
                    )
                },
            }
        ]
    fields_before = deepcopy(fields)

    with pytest.raises(
        JiraHelperOperationError, match="approved Media Services"
    ) as exc_info:
        IssueHelpers(cast(JiraAPI, api)).edit("PROJ-1", **edit_kwargs)

    _assert_exception_graph_and_traceback_locals_are_redacted(
        exc_info.value, first_media_id
    )
    assert fields == fields_before
    api.issues.edit_issue.assert_not_called()


@pytest.mark.parametrize("family", ["comment", "issue", "worklog"])
def test_managed_mutation_failures_discard_media_from_exception_graphs(
    family: str,
) -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )

    if family == "comment":
        api.comments.add_comment.side_effect = JiraConnectionError("network failure")

        def invoke() -> None:
            CommentHelpers(cast(JiraAPI, api)).add(
                "PROJ-1", f"![screen]({_CONTENT_URL})"
            )

        mutation = api.comments.add_comment
    elif family == "issue":
        api.issues.edit_issue.side_effect = JiraConnectionError("network failure")

        def invoke() -> None:
            IssueHelpers(cast(JiraAPI, api)).edit(
                "PROJ-1", description=f"![screen]({_CONTENT_URL})"
            )

        mutation = api.issues.edit_issue
    else:
        api.worklogs.add_worklog.side_effect = JiraConnectionError("network failure")

        def invoke() -> None:
            WorklogHelpers(cast(JiraAPI, api)).add(
                "PROJ-1", "1h", comment=f"![screen]({_CONTENT_URL})"
            )

        mutation = api.worklogs.add_worklog

    with pytest.raises(JiraHelperOperationError) as exc_info:
        invoke()

    assert exc_info.value.details == {
        "stage": "mutation_request",
        "mutation_may_have_succeeded": True,
        "issue_key": "PROJ-1",
    }
    _assert_exception_graph_and_traceback_locals_are_redacted(exc_info.value, _MEDIA_ID)
    mutation.assert_called_once()


@pytest.mark.parametrize("family", ["comment", "issue", "worklog"])
def test_managed_persisted_readback_failures_discard_media_from_exception_graphs(
    family: str,
) -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [_attachment()]
    api.attachments._get_attachment_content_redirect_location.return_value = (
        _MEDIA_LOCATION
    )

    def malformed_document(document: dict[str, Any]) -> dict[str, Any]:
        persisted = deepcopy(document)
        del persisted["content"][0]["content"][0]["attrs"]["width"]
        return persisted

    if family == "comment":
        api.comments.add_comment.side_effect = lambda **kwargs: {
            "id": "10000",
            "body": malformed_document(kwargs["body"]),
        }

        def invoke() -> None:
            CommentHelpers(cast(JiraAPI, api)).add(
                "PROJ-1", f"![screen]({_CONTENT_URL})"
            )

        mutation = api.comments.add_comment
    elif family == "issue":
        submitted: dict[str, Any] = {}

        def edit_issue(**kwargs: Any) -> None:
            submitted.update(kwargs["fields"])
            return None

        api.issues.edit_issue.side_effect = edit_issue
        api.issues.get_issue.side_effect = lambda **_kwargs: {
            "fields": {"description": malformed_document(submitted["description"])}
        }

        def invoke() -> None:
            IssueHelpers(cast(JiraAPI, api)).edit(
                "PROJ-1", description=f"![screen]({_CONTENT_URL})"
            )

        mutation = api.issues.edit_issue
    else:
        api.worklogs.add_worklog.side_effect = lambda **kwargs: {
            "id": "10001",
            "comment": malformed_document(kwargs["comment"]),
        }

        def invoke() -> None:
            WorklogHelpers(cast(JiraAPI, api)).add(
                "PROJ-1", "1h", comment=f"![screen]({_CONTENT_URL})"
            )

        mutation = api.worklogs.add_worklog

    with pytest.raises(JiraHelperOperationError) as exc_info:
        invoke()

    assert exc_info.value.details == {
        "stage": "persisted_readback",
        "issue_key": "PROJ-1",
        "mutation_may_have_succeeded": True,
    }
    _assert_exception_graph_and_traceback_locals_are_redacted(exc_info.value, _MEDIA_ID)
    mutation.assert_called_once()
