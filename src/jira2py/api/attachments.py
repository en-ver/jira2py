"""Attachments API implementation."""

from collections.abc import Mapping
from typing import Any

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
        *,
        redirect: bool | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> bytes:
        """Download raw bytes for a Jira attachment.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-content-id-get

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            redirect: Optional explicit ``redirect`` query parameter.
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            Raw attachment content bytes.
        """
        params = {"redirect": redirect} if redirect is not None else None
        return self._client._request_jira_bytes(
            method="GET",
            context_path=f"attachment/content/{attachment_id}",
            params=params,
            extra_params=extra_params,
            follow_redirects=True,
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
