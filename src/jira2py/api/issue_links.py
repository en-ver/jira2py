"""Issue Links API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import ApiBase


class IssueLinks(ApiBase):
    """Issue Links API — create, delete, and list issue links/types."""

    def get_issue_links(
        self,
        issue_id: str,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """List issue links on a Jira issue.

        Jira Cloud issues endpoint:
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get

        Args:
            issue_id: The ID or key of the issue (e.g., "PROJ-123").
            extra_params: Additional query parameters. Takes priority over named parameters.

        Returns:
            A list of issue-link objects from the issue ``issuelinks`` field.
        """
        issue = self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path=f"issue/{issue_id}",
                params={"fields": "issuelinks"},
                extra_params=extra_params,
            )
        )
        fields = issue.get("fields")
        links = fields.get("issuelinks", []) if isinstance(fields, dict) else []
        return self._as_list(links)

    def get_link_types(self) -> dict[str, Any]:
        """Get all available issue link types.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-link-types/#api-rest-api-3-issuelinktype-get

        Returns:
            Dictionary with "issueLinkTypes" containing link type objects.
        """
        return self._as_dict(
            self._client._request_jira(
                method="GET",
                context_path="issueLinkType",
            )
        )

    def create_link(
        self,
        link_type_name: str,
        inward_issue_key: str,
        outward_issue_key: str,
    ) -> None:
        """Create an issue link between two issues.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-post

        Args:
            link_type_name: Link type name (e.g., "Blocks", "Clones", "Duplicate").
            inward_issue_key: Key of the inward issue (e.g., "PROJ-123").
            outward_issue_key: Key of the outward issue (e.g., "PROJ-456").

        Returns:
            None. Jira returns 201 Created with no response body.
        """
        self._client._request_jira(
            method="POST",
            context_path="issueLink",
            data={
                "type": {"name": link_type_name},
                "inwardIssue": {"key": inward_issue_key},
                "outwardIssue": {"key": outward_issue_key},
            },
        )

    def delete_link(self, link_id: str) -> None:
        """Delete an issue link.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-linkid-delete

        Args:
            link_id: The ID of the issue link to delete.
        """
        self._client._request_jira(
            method="DELETE",
            context_path=f"issueLink/{link_id}",
        )
