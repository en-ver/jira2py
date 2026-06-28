"""Grouped issue-link helper operations for jira2py."""

from __future__ import annotations

from jira2py.api import JiraAPI

from ._text import format_issue_link_list
from ._validation import require_non_empty_string
from .errors import JiraHelperOperationError
from .models import IssueLink
from .results import HelperResult


class LinkHelpers:
    """High-level grouped helpers for Jira issue links."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def list(self, issue_key: str) -> HelperResult:
        """List issue links on a Jira issue."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")

        try:
            links_raw = self.api.issue_links.get_issue_links(issue_id=issue_key)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch issue links for {issue_key}: {exc}"
            ) from exc

        links = [IssueLink.model_validate(link) for link in links_raw]
        data = {"issue_key": issue_key, "links": links_raw}
        return HelperResult.with_data(format_issue_link_list(issue_key, links), data)

    def types(self) -> HelperResult:
        """List available Jira issue link types."""
        try:
            data = self.api.issue_links.get_link_types()
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch link types: {exc}"
            ) from exc

        link_types = data.get("issueLinkTypes", [])
        lines = [
            (
                f'- **{link_type["name"]}**: outward="{link_type.get("outward", "")}", '
                f'inward="{link_type.get("inward", "")}"'
            )
            for link_type in link_types
        ]
        text = "\n".join(lines) if lines else "No link types configured."
        return HelperResult.with_data(text, data)

    def create(
        self,
        link_type: str,
        outward_issue_key: str,
        inward_issue_key: str,
    ) -> HelperResult:
        """Create a link between two Jira issues."""
        link_type = require_non_empty_string(link_type, field_name="link_type")
        outward_issue_key = require_non_empty_string(
            outward_issue_key,
            field_name="outward_issue_key",
        )
        inward_issue_key = require_non_empty_string(
            inward_issue_key,
            field_name="inward_issue_key",
        )

        try:
            self.api.issue_links.create_link(
                link_type_name=link_type,
                inward_issue_key=inward_issue_key,
                outward_issue_key=outward_issue_key,
            )
        except Exception as exc:
            raise JiraHelperOperationError(f"Failed to create link: {exc}") from exc

        data = {
            "status": "created",
            "link_type": link_type,
            "outward_issue": outward_issue_key,
            "inward_issue": inward_issue_key,
        }
        text = (
            f"Created link: {outward_issue_key} {link_type.lower()} {inward_issue_key}"
        )
        return HelperResult.with_data(text, data)

    def delete(self, link_id: str) -> HelperResult:
        """Delete a Jira issue link."""
        link_id = require_non_empty_string(link_id, field_name="link_id")

        try:
            self.api.issue_links.delete_link(link_id=link_id)
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to delete link {link_id}: {exc}"
            ) from exc

        return HelperResult.with_data(
            f"Deleted issue link {link_id}",
            {"status": "deleted", "link_id": link_id},
        )


__all__ = ["LinkHelpers"]
