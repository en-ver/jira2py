from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import BinaryIO, cast
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


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(attachments=Mock())


def _metadata(*, filename: str = "report.csv", size: object = 11) -> dict[str, object]:
    return {
        "id": "10001",
        "filename": filename,
        "mimeType": "text/csv",
        "size": size,
        "content": "https://untrusted.example/never-used",
    }


def _stream_bytes(content: bytes):
    def stream(
        attachment_id: str,
        destination: BinaryIO,
        *,
        max_bytes: int,
        expected_size: int | None,
    ) -> int:
        assert attachment_id == "10001"
        assert len(content) <= max_bytes
        assert expected_size is None or len(content) == expected_size
        destination.write(content)
        return len(content)

    return stream


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


def test_download_streams_to_same_directory_temporary_file_and_replaces_atomically(
    tmp_path: Path,
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(
        filename="nested/report.csv"
    )
    temporary_paths: list[Path] = []

    def stream(
        _attachment_id: str,
        destination: BinaryIO,
        *,
        max_bytes: int,
        expected_size: int | None,
    ) -> int:
        temporary_paths.append(Path(destination.name))
        assert max_bytes == 100 * 1024 * 1024
        assert expected_size == 11
        destination.write(b"hello world")
        return 11

    api.attachments.download_attachment_content.side_effect = stream
    target_directory = tmp_path / "downloads"
    target_directory.mkdir()
    final_path = target_directory / "report.csv"
    final_path.write_bytes(b"old")

    result = AttachmentHelpers(cast(JiraAPI, api)).download(
        "10001", directory=target_directory
    )

    assert final_path.read_bytes() == b"hello world"
    assert temporary_paths[0].parent == target_directory.resolve()
    assert not temporary_paths[0].exists()
    assert result.data == {
        "status": "downloaded",
        "attachment_id": "10001",
        "filename": "report.csv",
        "output_file": str(final_path),
        "size": 11,
        "mime_type": "text/csv",
    }
    assert isinstance(result.data, dict)
    assert "content_url" not in result.data


def test_download_success_does_not_unlink_consumed_temporary_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata()
    api.attachments.download_attachment_content.side_effect = _stream_bytes(
        b"hello world"
    )

    def unexpected_unlink(_path: Path, *args: object, **kwargs: object) -> None:
        raise AssertionError("successful replacement must not be followed by unlink")

    monkeypatch.setattr(Path, "unlink", unexpected_unlink)

    result = AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)

    assert (tmp_path / "report.csv").read_bytes() == b"hello world"
    assert isinstance(result.data, dict)
    assert result.data["status"] == "downloaded"


def test_download_creates_directory_and_uses_explicit_basename(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(
        filename="ignored.csv"
    )
    api.attachments.download_attachment_content.side_effect = _stream_bytes(
        b"hello world"
    )

    result = AttachmentHelpers(cast(JiraAPI, api)).download(
        "10001", directory=tmp_path / "new" / "downloads", filename="chosen.csv"
    )

    assert (
        tmp_path / "new" / "downloads" / "chosen.csv"
    ).read_bytes() == b"hello world"
    assert isinstance(result.data, dict)
    assert result.data["filename"] == "chosen.csv"


@pytest.mark.parametrize(
    "filename",
    [
        "",
        ".",
        "..",
        "nested/file",
        r"nested\file",
        "bad:name",
        "\x00bad",
        "bad\x7f",
        "bad\x85",
    ],
)
def test_download_rejects_unsafe_explicit_filename_before_metadata(
    filename: str,
) -> None:
    api = _make_api()

    with pytest.raises(JiraHelperValidationError, match="filename"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", filename=filename)

    api.attachments.get_attachment_metadata.assert_not_called()


def test_download_rejects_existing_non_directory_before_metadata(
    tmp_path: Path,
) -> None:
    api = _make_api()
    destination = tmp_path / "not-a-directory"
    destination.write_text("file")

    with pytest.raises(JiraHelperValidationError, match="not a directory"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=destination)

    api.attachments.get_attachment_metadata.assert_not_called()


def test_download_sanitizes_metadata_filename_and_fallback(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(
        filename="../bad:\x7fname\x85?.txt"
    )
    api.attachments.download_attachment_content.side_effect = _stream_bytes(
        b"hello world"
    )

    result = AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)

    assert isinstance(result.data, dict)
    assert result.data["filename"] == "bad__name__.txt"
    assert (tmp_path / "bad__name__.txt").read_bytes() == b"hello world"


def test_download_sanitizes_control_characters_in_fallback_filename(
    tmp_path: Path,
) -> None:
    attachment_id = "100\x7f\x85"
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(
        filename="", size=0
    )

    def empty_stream(
        actual_attachment_id: str,
        destination: BinaryIO,
        *,
        max_bytes: int,
        expected_size: int | None,
    ) -> int:
        assert actual_attachment_id == attachment_id
        assert max_bytes == 100 * 1024 * 1024
        assert expected_size == 0
        return destination.write(b"")

    api.attachments.download_attachment_content.side_effect = empty_stream

    result = AttachmentHelpers(cast(JiraAPI, api)).download(
        attachment_id, directory=tmp_path
    )

    assert isinstance(result.data, dict)
    assert result.data["filename"] == "attachment-100__"
    assert (tmp_path / "attachment-100__").exists()


def test_download_distinguishes_missing_and_zero_metadata_size(tmp_path: Path) -> None:
    api = _make_api()
    missing_size = _metadata()
    del missing_size["size"]
    api.attachments.get_attachment_metadata.return_value = missing_size
    api.attachments.download_attachment_content.side_effect = _stream_bytes(
        b"hello world"
    )

    AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)
    assert (
        api.attachments.download_attachment_content.call_args.kwargs["expected_size"]
        is None
    )

    api.attachments.reset_mock()
    api.attachments.get_attachment_metadata.return_value = _metadata(size=0)
    api.attachments.download_attachment_content.side_effect = _stream_bytes(b"")

    AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)
    assert (
        api.attachments.download_attachment_content.call_args.kwargs["expected_size"]
        == 0
    )


@pytest.mark.parametrize("limit", [False, 0, -1, 1.5])
def test_download_rejects_invalid_max_download_before_metadata(limit: object) -> None:
    api = _make_api()

    with pytest.raises(JiraHelperValidationError, match="max_download"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", max_download=limit)  # type: ignore[arg-type]

    api.attachments.get_attachment_metadata.assert_not_called()


@pytest.mark.parametrize("size", [True, "bad", None, [], 1.5, -1])
def test_download_rejects_malformed_metadata_size_before_output(
    tmp_path: Path, size: object
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(size=size)

    with pytest.raises(AttachmentDownloadError, match="invalid size"):
        AttachmentHelpers(cast(JiraAPI, api)).download(
            "10001", directory=tmp_path / "not-created"
        )

    assert not (tmp_path / "not-created").exists()
    api.attachments.download_attachment_content.assert_not_called()


def test_download_rejects_oversized_metadata_before_output(tmp_path: Path) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata(size=12)

    with pytest.raises(AttachmentError, match="too large"):
        AttachmentHelpers(cast(JiraAPI, api)).download(
            "10001", directory=tmp_path / "not-created", max_download=11
        )

    assert not (tmp_path / "not-created").exists()
    api.attachments.download_attachment_content.assert_not_called()


def test_download_failure_preserves_existing_file_and_removes_temporary_file(
    tmp_path: Path,
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata()
    destination = tmp_path / "report.csv"
    destination.write_bytes(b"old")
    temporary_paths: list[Path] = []

    def broken_stream(
        _attachment_id: str,
        handle: BinaryIO,
        **_kwargs: object,
    ) -> int:
        temporary_paths.append(Path(handle.name))
        handle.write(b"partial")
        raise RuntimeError("stream failed")

    api.attachments.download_attachment_content.side_effect = broken_stream

    with pytest.raises(AttachmentDownloadError, match="stream failed"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)

    assert destination.read_bytes() == b"old"
    assert not temporary_paths[0].exists()


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
def test_download_interruption_cleans_temporary_file(
    tmp_path: Path, interruption: type[BaseException]
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata()
    temporary_paths: list[Path] = []

    def interrupted_stream(
        _attachment_id: str, destination: BinaryIO, **_kwargs: object
    ) -> int:
        temporary_paths.append(Path(destination.name))
        destination.write(b"partial")
        raise interruption()

    api.attachments.download_attachment_content.side_effect = interrupted_stream

    with pytest.raises(interruption):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)

    assert not temporary_paths[0].exists()


def test_download_replacement_failure_preserves_existing_file_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.return_value = _metadata()
    api.attachments.download_attachment_content.side_effect = _stream_bytes(
        b"hello world"
    )
    destination = tmp_path / "report.csv"
    destination.write_bytes(b"old")
    monkeypatch.setattr(
        os, "replace", lambda *_args: (_ for _ in ()).throw(OSError("no"))
    )

    with pytest.raises(AttachmentDownloadError, match="no"):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001", directory=tmp_path)

    assert destination.read_bytes() == b"old"
    assert list(tmp_path.glob(".jira2py-*")) == []


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

    result = AttachmentHelpers(cast(JiraAPI, api)).upload("PROJ-1", str(upload_file))

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


def test_download_wraps_metadata_errors() -> None:
    api = _make_api()
    api.attachments.get_attachment_metadata.side_effect = RuntimeError("boom")

    with pytest.raises(
        JiraHelperOperationError, match="Failed to fetch attachment metadata 10001"
    ):
        AttachmentHelpers(cast(JiraAPI, api)).download("10001")
