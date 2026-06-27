from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.attachments import AttachmentHelpers
from jira2py.helpers.errors import (
    AttachmentDownloadError,
    AttachmentError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)
from jira2py.helpers.models import AttachmentDownloadPlan


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        attachments=Mock(),
    )


def test_validate_id_rejects_blank_attachment_id() -> None:
    helper = AttachmentHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="attachment_id"):
        helper.validate_id("   ")


def test_list_attachments_formats_explicit_issue_attachment_list() -> None:
    api = _make_api()
    api.attachments.get_issue_attachments.return_value = [
        {
            "id": "10001",
            "filename": "debug.log",
            "mimeType": "text/plain",
            "size": 1536,
        }
    ]

    result = AttachmentHelpers(cast(JiraAPI, api)).list("PROJ-1")

    api.attachments.get_issue_attachments.assert_called_once_with(issue_id="PROJ-1")
    assert result.data == {
        "issue_key": "PROJ-1",
        "attachments": api.attachments.get_issue_attachments.return_value,
    }
    assert result.text == (
        "Attachments on PROJ-1: 1 total\n\n- debug.log (id: 10001, text/plain, 1.5 KB)"
    )


def test_read_attachment_formats_metadata() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": "10001",
        "filename": "debug.log",
        "mimeType": "text/plain",
        "size": 1536,
        "created": "2026-01-02T03:04:05.000+0000",
        "author": {"displayName": "Alice"},
        "content": "https://cdn.example.test/10001",
    }

    result = AttachmentHelpers(cast(JiraAPI, api)).read("10001")

    api.attachments.get_attachment_metadata.assert_called_once_with(
        attachment_id="10001"
    )
    assert result.data == api.attachments.get_attachment_metadata.return_value
    assert result.text == (
        "Attachment 10001: debug.log\n"
        "Type: text/plain\n"
        "Size: 1.5 KB\n"
        "Created: 2026-01-02\n"
        "Author: Alice\n"
        "Content URL: https://cdn.example.test/10001"
    )


def test_plan_download_fetches_metadata_and_plans_output(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": "10001",
        "filename": "../bad:name?.txt",
        "mimeType": "text/plain",
        "size": 1536,
        "content": "https://cdn.example.test/10001",
    }
    helper = AttachmentHelpers(cast(JiraAPI, api))

    result = helper.plan_download(
        "10001",
        output_path=str(tmp_path / "downloads") + "/",
    )

    api.attachments.get_attachment_metadata.assert_called_once_with(
        attachment_id="10001"
    )
    assert isinstance(result.data, AttachmentDownloadPlan)
    assert result.data.attachment_id == "10001"
    assert result.data.filename == "bad_name_.txt"
    assert result.data.output_file == str(
        (tmp_path / "downloads" / "bad_name_.txt").resolve()
    )
    assert (
        result.data.resolved_output
        == (tmp_path / "downloads" / "bad_name_.txt").resolve()
    )
    assert result.data.meta.id == 10001
    assert result.data.content_url == "https://cdn.example.test/10001"
    assert "Attachment ready: bad_name_.txt" in result.text
    assert "Size: 1.5 KB" in result.text


def test_plan_download_uses_existing_directory_output_path(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": 10002,
        "filename": "report.csv",
        "mimeType": "text/csv",
        "size": 64,
    }
    output_dir = tmp_path / "exports"
    output_dir.mkdir()

    result = AttachmentHelpers(cast(JiraAPI, api)).plan_download(
        "10002",
        output_path=str(output_dir),
    )

    assert isinstance(result.data, AttachmentDownloadPlan)
    assert result.data.output_file == str((output_dir / "report.csv").resolve())
    assert result.data.content_url == (
        "https://example.atlassian.net/rest/api/3/attachment/content/10002"
    )


def test_download_attachment_writes_bytes_to_safe_output_path(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": "10003",
        "filename": "nested/report.csv",
        "mimeType": "text/csv",
        "size": 11,
    }
    api.attachments.download_attachment_content.return_value = b"hello world"

    result = AttachmentHelpers(cast(JiraAPI, api)).download(
        "10003",
        output_path=str(tmp_path / "downloads") + "/",
    )

    output_file = (tmp_path / "downloads" / "report.csv").resolve()
    assert output_file.read_bytes() == b"hello world"
    api.attachments.download_attachment_content.assert_called_once_with(
        attachment_id="10003"
    )
    assert result.data == {
        "status": "downloaded",
        "attachment_id": "10003",
        "filename": "report.csv",
        "output_file": str(output_file),
        "size": 11,
        "mime_type": "text/csv",
        "content_url": "https://example.atlassian.net/rest/api/3/attachment/content/10003",
    }
    assert result.text == (
        "Downloaded attachment report.csv (id: 10003)\n"
        "Type: text/csv\n"
        "Size: 11 bytes\n"
        f"Output: {output_file}"
    )


def test_download_attachment_rejects_oversized_bytes_after_fetch() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": "10003",
        "filename": "report.csv",
        "mimeType": "text/csv",
        "size": 5,
    }
    api.attachments.download_attachment_content.return_value = b"123456"

    with pytest.raises(AttachmentDownloadError, match="exceeded max allowed size"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10003", max_download=5)


def test_plan_download_rejects_invalid_limit_and_large_files() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = {
        "id": 10003,
        "filename": "archive.zip",
        "mimeType": "application/zip",
        "size": 4096,
    }
    helper = AttachmentHelpers(cast(JiraAPI, api))

    with pytest.raises(JiraHelperValidationError, match="max_download"):
        helper.plan_download("10003", max_download=0)

    with pytest.raises(AttachmentError, match="Attachment too large"):
        helper.plan_download("10003", max_download=1024)


def test_upload_attachment_reads_local_file_and_returns_created_metadata(
    tmp_path: Path,
) -> None:
    api = _make_api()
    upload_file = tmp_path / "report.txt"
    upload_file.write_text("hello world", encoding="utf-8")
    api.attachments.add_attachment.return_value = [
        {
            "id": "10005",
            "filename": "report.txt",
            "mimeType": "text/plain",
            "size": 11,
        }
    ]

    result = AttachmentHelpers(cast(JiraAPI, api)).upload(
        "PROJ-1",
        str(upload_file),
    )

    api.attachments.add_attachment.assert_called_once_with(
        issue_id="PROJ-1",
        filename="report.txt",
        content=b"hello world",
        content_type="text/plain",
    )
    assert result.data == api.attachments.add_attachment.return_value
    assert result.text == (
        "Uploaded attachment to PROJ-1: report.txt\n"
        "Attachment ID: 10005\n"
        "Type: text/plain\n"
        "Size: 11 bytes"
    )


def test_upload_attachment_validates_input_path(tmp_path: Path) -> None:
    helper = AttachmentHelpers(cast(JiraAPI, _make_api()))

    with pytest.raises(JiraHelperValidationError, match="does not exist"):
        helper.upload("PROJ-1", str(tmp_path / "missing.txt"))

    with pytest.raises(JiraHelperValidationError, match="not a file"):
        helper.upload("PROJ-1", str(tmp_path))


def test_delete_attachment_returns_explicit_id() -> None:
    api = _make_api()

    result = AttachmentHelpers(cast(JiraAPI, api)).delete("10006")

    api.attachments.delete_attachment.assert_called_once_with(attachment_id="10006")
    assert result.data == {"status": "deleted", "attachment_id": "10006"}
    assert result.text == "Deleted attachment 10006"


def test_plan_download_wraps_metadata_errors() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.side_effect = RuntimeError("boom")

    with pytest.raises(
        JiraHelperOperationError,
        match="Failed to fetch attachment metadata 10004",
    ):
        AttachmentHelpers(cast(JiraAPI, api)).plan_download("10004")
