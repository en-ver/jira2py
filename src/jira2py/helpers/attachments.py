"""Grouped attachment helper operations for jira2py."""

from __future__ import annotations

import mimetypes
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO, cast

from jira2py.api import JiraAPI

from ._text import format_attachment_list, format_attachment_metadata
from ._utils import format_size
from ._validation import require_non_empty_string
from .errors import (
    AttachmentDownloadError,
    AttachmentError,
    JiraHelperOperationError,
    JiraHelperValidationError,
)
from .models import AttachmentMeta
from .results import HelperResult

DEFAULT_MAX_DOWNLOAD = 100 * 1024 * 1024  # 100 MB
_INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]')


class AttachmentHelpers:
    """High-level grouped helpers for Jira attachments."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def validate_id(self, attachment_id: str) -> None:
        """Validate attachment-id input without calling Jira."""
        require_non_empty_string(attachment_id, field_name="attachment_id")

    def list(self, issue_key: str) -> HelperResult:
        """List attachments on a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")

        try:
            attachments_raw = self.api.attachments.get_issue_attachments(
                issue_id=issue_key
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch attachments for {issue_key}: {exc}"
            ) from exc

        attachments = [
            AttachmentMeta.model_validate(attachment) for attachment in attachments_raw
        ]
        data = {"issue_key": issue_key, "attachments": attachments_raw}
        return HelperResult.with_data(
            format_attachment_list(issue_key, attachments),
            data,
        )

    def read(self, attachment_id: str) -> HelperResult:
        """Read metadata for a single Jira attachment."""
        self.validate_id(attachment_id)

        try:
            data = self.api.attachments.get_attachment_metadata(
                attachment_id=attachment_id
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch attachment metadata {attachment_id}: {exc}"
            ) from exc

        attachment = AttachmentMeta.model_validate(data)
        return HelperResult.with_data(format_attachment_metadata(attachment), data)

    def download(
        self,
        attachment_id: str,
        *,
        directory: str | os.PathLike[str] = ".",
        filename: str | None = None,
        max_download: int = DEFAULT_MAX_DOWNLOAD,
    ) -> HelperResult:
        """Download an attachment atomically into a directory-owned destination."""
        self.validate_id(attachment_id)
        _validate_max_download(max_download)
        resolved_directory = _resolve_download_directory(directory)
        if filename is not None:
            _validate_explicit_filename(filename)

        try:
            data = self.api.attachments.get_attachment_metadata(
                attachment_id=attachment_id
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch attachment metadata {attachment_id}: {exc}"
            ) from exc

        expected_size = _metadata_expected_size(data, attachment_id)
        meta = AttachmentMeta.model_validate(data)
        if expected_size is not None and expected_size > max_download:
            raise AttachmentError(
                f"Attachment too large: {format_size(expected_size)}. "
                f"Max allowed: {format_size(max_download)}"
            )

        effective_filename = (
            filename
            if filename is not None
            else _sanitize_attachment_filename(meta.filename, attachment_id)
        )
        final_path = resolved_directory / effective_filename
        try:
            resolved_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise AttachmentDownloadError(
                f"Failed to create download directory {resolved_directory}: {exc}"
            ) from exc

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, dir=resolved_directory, prefix=".jira2py-"
            ) as destination:
                temporary_path = Path(destination.name)
                observed_size = self.api.attachments.download_attachment_content(
                    attachment_id,
                    cast(BinaryIO, destination),
                    max_bytes=max_download,
                    expected_size=expected_size,
                )
            os.replace(temporary_path, final_path)
            temporary_path = None
        except Exception as exc:
            raise AttachmentDownloadError(
                f"Failed to download attachment {attachment_id}: {exc}"
            ) from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        output_file = str(final_path)
        result_data = {
            "status": "downloaded",
            "attachment_id": attachment_id,
            "filename": effective_filename,
            "output_file": output_file,
            "size": observed_size,
            "mime_type": meta.mimeType,
        }
        text = (
            f"Downloaded attachment {effective_filename} (id: {attachment_id})\n"
            f"Type: {meta.mimeType}\n"
            f"Size: {format_size(observed_size)}\n"
            f"Output: {output_file}"
        )
        return HelperResult.with_data(text, result_data)

    def upload(self, issue_key: str, file_path: str) -> HelperResult:
        """Upload a local file as a Jira issue attachment."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        file_path = require_non_empty_string(file_path, field_name="file_path")
        path = Path(file_path).expanduser()

        if not path.exists():
            raise JiraHelperValidationError(f"Attachment file does not exist: {path}")
        if not path.is_file():
            raise JiraHelperValidationError(f"Attachment path is not a file: {path}")

        try:
            content = path.read_bytes()
        except OSError as exc:
            raise JiraHelperOperationError(
                f"Failed to read attachment file {path}: {exc}"
            ) from exc

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        try:
            data = self.api.attachments.add_attachment(
                issue_id=issue_key,
                filename=path.name,
                content=content,
                content_type=content_type,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to upload attachment to {issue_key}: {exc}"
            ) from exc

        attachments = [AttachmentMeta.model_validate(attachment) for attachment in data]
        count = len(attachments)
        if count == 0:
            text = f"Uploaded attachment to {issue_key}: {path.name}"
        elif count == 1:
            attachment = attachments[0]
            text = (
                f"Uploaded attachment to {issue_key}: {attachment.filename or path.name}\n"
                f"Attachment ID: {attachment.id}\n"
                f"Type: {attachment.mimeType}\n"
                f"Size: {format_size(attachment.size)}"
            )
        else:
            text = f"Uploaded {count} attachment(s) to {issue_key}: {path.name}"
        return HelperResult.with_data(text, data)

    def delete(self, attachment_id: str) -> HelperResult:
        """Delete a Jira attachment by ID."""
        self.validate_id(attachment_id)

        try:
            self.api.attachments.delete_attachment(attachment_id=attachment_id)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to delete attachment {attachment_id}: {exc}"
            ) from exc

        return HelperResult.with_data(
            f"Deleted attachment {attachment_id}",
            {"status": "deleted", "attachment_id": attachment_id},
        )


def _validate_max_download(max_download: int) -> None:
    if (
        isinstance(max_download, bool)
        or not isinstance(max_download, int)
        or max_download < 1
    ):
        raise JiraHelperValidationError("max_download must be an integer at least 1.")


def _resolve_download_directory(directory: str | os.PathLike[str]) -> Path:
    try:
        resolved_directory = Path(directory).expanduser().resolve(strict=False)
    except (TypeError, OSError) as exc:
        raise JiraHelperValidationError(
            "directory must be a valid local path."
        ) from exc
    if resolved_directory.exists() and not resolved_directory.is_dir():
        raise JiraHelperValidationError(
            f"Download directory is not a directory: {resolved_directory}"
        )
    return resolved_directory


def _validate_explicit_filename(filename: str) -> None:
    if (
        not isinstance(filename, str)
        or not filename
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
        or _INVALID_FILENAME_CHARS_RE.search(filename) is not None
        or Path(filename).is_absolute()
    ):
        raise JiraHelperValidationError("filename must be a safe non-empty basename.")


def _metadata_expected_size(data: dict[str, object], attachment_id: str) -> int | None:
    if "size" not in data:
        return None
    size = data["size"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise AttachmentDownloadError(
            f"Attachment {attachment_id} metadata has an invalid size."
        )
    return size


def _sanitize_attachment_filename(filename: str | None, attachment_id: str) -> str:
    raw_filename = (filename or _attachment_filename_fallback(attachment_id)).replace(
        "\\", "/"
    )
    basename = raw_filename.split("/")[-1]
    sanitized = _INVALID_FILENAME_CHARS_RE.sub("_", basename).strip().strip(".")
    return sanitized or _attachment_filename_fallback(attachment_id)


def _attachment_filename_fallback(attachment_id: str) -> str:
    safe_id = _INVALID_FILENAME_CHARS_RE.sub("_", attachment_id).strip().strip(".")
    return f"attachment-{safe_id or 'download'}"


__all__ = ["AttachmentHelpers", "DEFAULT_MAX_DOWNLOAD"]
