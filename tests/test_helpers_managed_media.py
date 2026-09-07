from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import httpx
import pytest

from jira2py import JiraAPI
from jira2py.api.attachments import Attachments
from jira2py.helpers._managed_media import (
    _classify_attachment_content_url,
    _configured_jira_origin,
    _media_id_from_redirect_location,
)
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


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        attachments=Mock(),
        comments=Mock(),
        fields=Mock(),
        issues=Mock(),
        worklogs=Mock(),
    )


def _attachment(
    attachment_id: str = "10000", mime_type: str = "image/png"
) -> dict[str, str]:
    return {"id": attachment_id, "mimeType": mime_type, "filename": "screen.png"}


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
    assert set(media[0]) == {"type", "id", "collection", "alt"}
    assert media[1]["alt"] == "again"
    assert (
        captured["fields"]["environment"]["content"][0]["content"][0]["attrs"][
            "collection"
        ]
        == ""
    )


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
