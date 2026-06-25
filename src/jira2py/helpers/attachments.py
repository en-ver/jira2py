"""Grouped attachment helper operations for jira2py."""

from __future__ import annotations

import os
import re
from pathlib import Path

from jira2py.api import JiraAPI

from ._utils import format_size
from ._validation import require_non_empty_string
from .errors import AttachmentError, JiraHelperOperationError, JiraHelperValidationError
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
