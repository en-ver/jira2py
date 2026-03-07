"""Attachments API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import ApiBase


class Attachments(ApiBase):
    """Attachments API — get attachment metadata."""

    def get_attachment_metadata(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a Jira attachment.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            extra_params: Additional query parameters.

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
