from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.helpers.attachments import AttachmentHelpers
from jira2py.helpers.errors import (
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


def test_plan_download_wraps_metadata_errors() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.side_effect = RuntimeError("boom")

    with pytest.raises(
        JiraHelperOperationError,
        match="Failed to fetch attachment metadata 10004",
    ):
        AttachmentHelpers(cast(JiraAPI, api)).plan_download("10004")
