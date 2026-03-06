"""Unified Issue Links API implementation using generic pattern."""

from typing import Any, TypeVar

from pydantic import validate_call

from jira2py.client import JiraClientAsync, JiraClientSync

from .api_base import ApiBase

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class IssueLinksBase(ApiBase[T]):
    """Base class for Issue Links API - contains shared business logic."""

    def _get_link_types_request_config(self) -> dict[str, Any]:
        """Prepare request configuration for get_link_types.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "GET",
            "context_path": "issueLinkType",
        }

    def _create_link_request_config(
        self,
        link_type_name: str,
        inward_issue_key: str,
        outward_issue_key: str,
    ) -> dict[str, Any]:
        """Prepare request configuration for create_link.

        Args:
            link_type_name: The name of the link type (e.g., "Blocks", "Clones").
            inward_issue_key: The key of the inward issue (e.g., "PROJ-123").
            outward_issue_key: The key of the outward issue (e.g., "PROJ-456").

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "POST",
            "context_path": "issueLink",
            "data": {
                "type": {"name": link_type_name},
                "inwardIssue": {"key": inward_issue_key},
                "outwardIssue": {"key": outward_issue_key},
            },
        }

    def _delete_link_request_config(
        self,
        link_id: str,
    ) -> dict[str, Any]:
        """Prepare request configuration for delete_link.

        Args:
            link_id: The ID of the issue link to delete.

        Returns:
            Dictionary with request configuration.
        """
        return {
            "method": "DELETE",
            "context_path": f"issueLink/{link_id}",
        }


class IssueLinks(IssueLinksBase[JiraClientSync]):
    """Synchronous Issue Links API implementation."""

    @validate_call
    def get_link_types(self) -> dict[str, Any]:
        """Get all available issue link types.

        Returns the list of issue link types configured in the Jira instance,
        including their names, inward and outward descriptions.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-link-types/#api-rest-api-3-issuelinktype-get

        Returns:
            A dictionary containing an "issueLinkTypes" key with a list of
            link type objects, each having id, name, inward, and outward fields.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> result = api.issue_links.get_link_types()
            >>> [lt["name"] for lt in result["issueLinkTypes"]]
            ['Blocks', 'Clones', 'Duplicate', 'Relates']
        """
        request_config = self._get_link_types_request_config()
        return self._as_dict(self._client._request_jira(**request_config))

    @validate_call
    def create_link(
        self,
        link_type_name: str,
        inward_issue_key: str,
        outward_issue_key: str,
    ) -> None:
        """Create an issue link between two issues.

        Creates a link of the specified type between two issues. The link direction
        is determined by which issue is inward vs outward. For example, with link type
        "Blocks": the outward issue "blocks" the inward issue.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-post

        Args:
            link_type_name: The name of the link type (e.g., "Blocks", "Clones", "Duplicate").
            inward_issue_key: The key of the inward issue (e.g., "PROJ-123").
            outward_issue_key: The key of the outward issue (e.g., "PROJ-456").

        Returns:
            None. Jira returns 201 Created with no response body.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If either issue is not found (404).
            JiraValidationError: If the link type or issue keys are invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> api.issue_links.create_link("Blocks", inward_issue_key="PROJ-456", outward_issue_key="PROJ-123")
        """
        request_config = self._create_link_request_config(
            link_type_name, inward_issue_key, outward_issue_key
        )
        self._client._request_jira(**request_config)

    @validate_call
    def delete_link(
        self,
        link_id: str,
    ) -> None:
        """Delete an issue link.

        Deletes an issue link by its ID. The link ID can be obtained from
        the issue's issuelinks field.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-linkid-delete

        Args:
            link_id: The ID of the issue link to delete.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the link is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.

        Example:
            >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
            >>> api.issue_links.delete_link("10001")
        """
        request_config = self._delete_link_request_config(link_id)
        self._client._request_jira(**request_config)


class IssueLinksAsync(IssueLinksBase[JiraClientAsync]):
    """Asynchronous Issue Links API implementation."""

    @validate_call
    async def get_link_types(self) -> dict[str, Any]:
        """Get all available issue link types (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-link-types/#api-rest-api-3-issuelinktype-get

        Returns:
            A dictionary containing an "issueLinkTypes" key with a list of
            link type objects, each having id, name, inward, and outward fields.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.
        """
        request_config = self._get_link_types_request_config()
        return self._as_dict(await self._client._request_jira(**request_config))

    @validate_call
    async def create_link(
        self,
        link_type_name: str,
        inward_issue_key: str,
        outward_issue_key: str,
    ) -> None:
        """Create an issue link between two issues (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-post

        Args:
            link_type_name: The name of the link type (e.g., "Blocks", "Clones", "Duplicate").
            inward_issue_key: The key of the inward issue (e.g., "PROJ-123").
            outward_issue_key: The key of the outward issue (e.g., "PROJ-456").

        Returns:
            None. Jira returns 201 Created with no response body.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If either issue is not found (404).
            JiraValidationError: If the link type or issue keys are invalid (400).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.
        """
        request_config = self._create_link_request_config(
            link_type_name, inward_issue_key, outward_issue_key
        )
        await self._client._request_jira(**request_config)

    @validate_call
    async def delete_link(
        self,
        link_id: str,
    ) -> None:
        """Delete an issue link (async version).

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-linkid-delete

        Args:
            link_id: The ID of the issue link to delete.

        Raises:
            JiraAuthenticationError: If authentication fails (401, 403).
            JiraNotFoundError: If the link is not found (404).
            JiraAPIError: For other API errors (4xx, 5xx).
            JiraConnectionError: For network or connection errors.
            JiraError: For any other jira2py errors.
        """
        request_config = self._delete_link_request_config(link_id)
        await self._client._request_jira(**request_config)
