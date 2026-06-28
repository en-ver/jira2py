"""Grouped attachment helper operations for jira2py."""

from __future__ import annotations

import mimetypes
import os
import re
from pathlib import Path

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
from .models import AttachmentDownloadPlan, AttachmentMeta
from .results import HelperResult

DEFAULT_MAX_DOWNLOAD = 100 * 1024 * 1024  # 100 MB
_INVALID_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


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

    def plan_download(
        self,
        attachment_id: str,
        *,
        output_path: str | None = None,
        max_download: int = DEFAULT_MAX_DOWNLOAD,
    ) -> HelperResult:
        """Fetch attachment metadata and plan a generic download destination."""
        self.validate_id(attachment_id)
        if max_download < 1:
            raise JiraHelperValidationError("max_download must be at least 1.")

        try:
            data = self.api.attachments.get_attachment_metadata(
                attachment_id=attachment_id
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch attachment metadata {attachment_id}: {exc}"
            ) from exc

        meta = AttachmentMeta.model_validate(data)
        if meta.size > max_download:
            raise AttachmentError(
                f"Attachment too large: {format_size(meta.size)}. "
                f"Max allowed: {format_size(max_download)}"
            )

        filename = _sanitize_attachment_filename(meta.filename, attachment_id)
        output_file, resolved_output = _build_attachment_output_path(
            filename,
            output_path=output_path,
        )
        plan = AttachmentDownloadPlan(
            attachment_id=attachment_id,
            filename=filename,
            output_file=output_file,
            resolved_output=resolved_output,
            meta=meta,
            content_url=(
                data.get("content")
                or f"{self.api.credentials.url}/rest/api/3/attachment/content/{attachment_id}"
            ),
        )
        return HelperResult.with_data(_format_download_plan(plan), plan)

    def download(
        self,
        attachment_id: str,
        *,
        output_path: str | None = None,
        max_download: int = DEFAULT_MAX_DOWNLOAD,
    ) -> HelperResult:
        """Download a Jira attachment to a local file."""
        plan_result = self.plan_download(
            attachment_id,
            output_path=output_path,
            max_download=max_download,
        )
        plan = plan_result.data
        if not isinstance(plan, AttachmentDownloadPlan):
            raise AttachmentDownloadError(
                f"Failed to plan download for attachment {attachment_id}"
            )

        try:
            content = self.api.attachments.download_attachment_content(
                attachment_id=attachment_id
            )
        except Exception as exc:
            raise AttachmentDownloadError(
                f"Failed to download attachment {attachment_id}: {exc}"
            ) from exc

        if len(content) > max_download:
            raise AttachmentDownloadError(
                "Downloaded attachment exceeded max allowed size: "
                f"{format_size(len(content))} > {format_size(max_download)}"
            )

        if "size" in plan.meta.model_fields_set and len(content) != plan.meta.size:
            raise AttachmentDownloadError(
                f"Downloaded attachment {attachment_id} size mismatch: "
                f"expected {plan.meta.size} bytes from metadata, "
                f"got {len(content)} bytes"
            )

        try:
            plan.resolved_output.parent.mkdir(parents=True, exist_ok=True)
            plan.resolved_output.write_bytes(content)
        except OSError as exc:
            raise AttachmentDownloadError(
                f"Failed to write attachment {attachment_id} to {plan.output_file}: {exc}"
            ) from exc

        data = {
            "status": "downloaded",
            "attachment_id": attachment_id,
            "filename": plan.filename,
            "output_file": plan.output_file,
            "size": len(content),
            "mime_type": plan.meta.mimeType,
            "content_url": plan.content_url,
        }
        text = (
            f"Downloaded attachment {plan.filename} (id: {attachment_id})\n"
            f"Type: {plan.meta.mimeType}\n"
            f"Size: {format_size(len(content))}\n"
            f"Output: {plan.output_file}"
        )
        return HelperResult.with_data(text, data)

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


def _sanitize_attachment_filename(filename: str | None, attachment_id: str) -> str:
    raw_filename = (filename or f"attachment-{attachment_id}").replace("\\", "/")
    basename = raw_filename.split("/")[-1]
    sanitized = _INVALID_FILENAME_CHARS_RE.sub("_", basename).strip().strip(".")
    if not sanitized or sanitized in {".", ".."}:
        return f"attachment-{attachment_id}"
    return sanitized


def _build_attachment_output_path(
    filename: str,
    *,
    output_path: str | None = None,
) -> tuple[str, Path]:
    if output_path:
        resolved = os.path.abspath(output_path)
        if os.path.isdir(resolved) or output_path.endswith(("/", "\\")):
            output_file = os.path.join(resolved, filename)
        else:
            output_file = resolved
    else:
        output_file = os.path.abspath(filename)

    return output_file, Path(output_file).resolve()


def _format_download_plan(plan: AttachmentDownloadPlan) -> str:
    return (
        f"Attachment ready: {plan.filename}\n"
        f"Type: {plan.meta.mimeType}\n"
        f"Size: {format_size(plan.meta.size)}\n"
        f"Planned output: {plan.output_file}"
    )


__all__ = ["AttachmentHelpers", "DEFAULT_MAX_DOWNLOAD"]
