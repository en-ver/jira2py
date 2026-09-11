"""Attachments API implementation."""

from collections.abc import Mapping
from typing import Any, BinaryIO

from jira2py.client.client_sync import _BoundedJiraContent

from .api_base import ApiBase


class Attachments(ApiBase):
    """Attachments API — list, read, download, upload, and delete attachments."""

    def get_issue_attachments(
        self,
        issue_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """List attachments on a Jira issue.

        Jira Cloud issues endpoint:
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            A list of attachment metadata objects from the issue ``attachment`` field.
        """
        issue = self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}",
                params={"fields": "attachment"},
                extra_params=extra_params,
            )
        )
        fields = issue.get("fields")
        attachments = fields.get("attachment", []) if isinstance(fields, dict) else []
        return self._as_list(attachments)

    def get_attachment_metadata(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a Jira attachment.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Attachment metadata: id, filename, size, mimeType, content URL, author, created.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"attachment/{attachment_id}",
                extra_params=extra_params,
            )
        )

    def download_attachment_content(
        self,
        attachment_id: str,
        destination: BinaryIO,
        *,
        max_bytes: int,
        expected_size: int | None = None,
        redirect: bool | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> int:
        """Stream a Jira attachment to a caller-owned binary destination.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-content-id-get

        The destination is not closed, flushed, rewound, truncated, or cleaned up.
        A failed transfer can leave partial data in it.

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            destination: Open binary destination that receives attachment bytes.
            max_bytes: Required positive cumulative transfer limit.
            expected_size: Optional exact expected byte count; zero requires empty content.
            redirect: Optional explicit ``redirect`` query parameter.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            The observed number of bytes written to ``destination``.
        """
        params = {"redirect": redirect} if redirect is not None else None
        return self._client._request_jira_stream_to(
            context_path=f"attachment/content/{attachment_id}",
            destination=destination,
            max_bytes=max_bytes,
            expected_size=expected_size,
            params=params,
            extra_params=extra_params,
            follow_redirects=True,
        )

    def _get_attachment_content_bounded(
        self,
        attachment_id: str,
        *,
        expected_size: int,
        max_bytes: int,
        byte_range: tuple[int, int] | None = None,
    ) -> _BoundedJiraContent:
        """Read private managed-media content without following redirects."""
        return self._client._request_jira_bounded_content(
            context_path=f"attachment/content/{attachment_id}",
            expected_size=expected_size,
            max_bytes=max_bytes,
            byte_range=byte_range,
        )

    def _get_attachment_content_redirect_location(self, attachment_id: str) -> str:
        """Return Jira's no-follow attachment redirect Location for internal use."""
        return self._client._request_jira_redirect_location(
            method="GET",
            context_path=f"attachment/content/{attachment_id}",
        )

    def add_attachment(
        self,
        issue_id: str,
        filename: str,
        content: bytes,
        *,
        content_type: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Upload an attachment to a Jira issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-issue-issueidorkey-attachments-post

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            filename: Filename to send to Jira.
            content: Raw file content bytes.
            content_type: Optional MIME type for the file.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            A list of created attachment metadata objects.
        """
        file_part: tuple[str, bytes] | tuple[str, bytes, str]
        if content_type:
            file_part = (filename, content, content_type)
        else:
            file_part = (filename, content)

        return self._as_list(
            self._client._request_jira(
                method="POST",
                context_path=f"issue/{issue_id}/attachments",
                extra_params=extra_params,
                headers={"X-Atlassian-Token": "no-check"},
                files={"file": file_part},
            )
        )

    def delete_attachment(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> None:
        """Delete a Jira attachment.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-delete

        Args:
            attachment_id: The ID of the attachment to delete.
            extra_params: Additional query parameters. Takes priority over named parameters.
        """
        self._client._request_jira(
            method="DELETE",
            context_path=f"attachment/{attachment_id}",
            extra_params=extra_params,
        )
