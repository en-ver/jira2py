"""Unified Attachments API implementation using generic pattern."""

from collections.abc import Mapping
from typing import Any, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class AttachmentsBase(ApiBase[T]):
    """Base class for Attachments API - contains shared business logic."""

    def _get_attachment_metadata_request_config(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Prepare request configuration for get_attachment_metadata.

        Args:
            attachment_id: The ID of the attachment.
            extra_params: Additional query parameters to include in the request.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": f"attachment/{attachment_id}",
            "extra_params": extra_params,
        }


class Attachments(AttachmentsBase[JiraClientSync]):
    """Synchronous Attachments API implementation."""

    @validate_call
    def get_attachment_metadata(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a Jira attachment.

        Returns metadata for the specified attachment, including filename, size,
        MIME type, author, and download URL. Does not return the attachment content.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing attachment metadata:
            - "id": The attachment ID
            - "filename": The file name
            - "size": The file size in bytes
            - "mimeType": The MIME type
            - "content": The download URL
            - "author": The user who attached the file
            - "created": The creation datetime

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the attachment is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> meta = api.attachments.get_attachment_metadata("10000")
            >>> print(f"{meta['filename']} ({meta['size']} bytes)")
        """
        request_config = self._get_attachment_metadata_request_config(
            attachment_id,
            extra_params,
        )
        return self._as_dict(self._client._request_jira(**request_config))


class AttachmentsAsync(AttachmentsBase[JiraClientAsync]):
    """Asynchronous Attachments API implementation."""

    @validate_call
    async def get_attachment_metadata(
        self,
        attachment_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get metadata for a Jira attachment (async version).

        Returns metadata for the specified attachment, including filename, size,
        MIME type, author, and download URL. Does not return the attachment content.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get

        Args:
            attachment_id: The ID of the attachment (e.g., "10000").
            extra_params: Additional query parameters to include in the request.
                Defaults to None.

        Returns:
            A dictionary containing attachment metadata:
            - "id": The attachment ID
            - "filename": The file name
            - "size": The file size in bytes
            - "mimeType": The MIME type
            - "content": The download URL
            - "author": The user who attached the file
            - "created": The creation datetime

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the attachment is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> meta = await api.attachments.get_attachment_metadata("10000")
            >>> print(f"{meta['filename']} ({meta['size']} bytes)")
        """
        request_config = self._get_attachment_metadata_request_config(
            attachment_id,
            extra_params,
        )
        return self._as_dict(await self._client._request_jira(**request_config))
