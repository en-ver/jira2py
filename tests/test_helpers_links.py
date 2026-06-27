from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

from jira2py import JiraAPI
from jira2py.helpers.links import LinkHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(issue_links=Mock())


def test_list_issue_links_formats_explicit_issue_links() -> None:
    api = _make_api()
    api.issue_links.get_issue_links.return_value = [
        {
            "id": "10000",
            "type": {
                "name": "Blocks",
                "outward": "blocks",
                "inward": "is blocked by",
            },
            "outwardIssue": {
                "key": "PROJ-2",
                "fields": {
                    "summary": "Linked issue",
                    "status": {"name": "In Progress"},
                },
            },
        }
    ]

    result = LinkHelpers(cast(JiraAPI, api)).list("PROJ-1")

    api.issue_links.get_issue_links.assert_called_once_with(issue_id="PROJ-1")
    assert result.data == {
        "issue_key": "PROJ-1",
        "links": api.issue_links.get_issue_links.return_value,
    }
    assert result.text == (
        "Issue links on PROJ-1: 1 total\n\n"
        "- blocks PROJ-2: Linked issue [In Progress] (link id: 10000)"
    )


def test_link_types_formats_available_types() -> None:
    api = _make_api()
    api.issue_links.get_link_types.return_value = {
        "issueLinkTypes": [
            {
                "name": "Blocks",
                "outward": "blocks",
                "inward": "is blocked by",
            }
        ]
    }

    result = LinkHelpers(cast(JiraAPI, api)).types()

    assert result.text == '- **Blocks**: outward="blocks", inward="is blocked by"'
    assert result.data == api.issue_links.get_link_types.return_value


def test_create_and_delete_link_delegate_to_jira_api() -> None:
    api = _make_api()
    helper = LinkHelpers(cast(JiraAPI, api))

    create_result = helper.create("Blocks", "PROJ-1", "PROJ-2")
    delete_result = helper.delete("10000")

    api.issue_links.create_link.assert_called_once_with(
        link_type_name="Blocks",
        inward_issue_key="PROJ-2",
        outward_issue_key="PROJ-1",
    )
    api.issue_links.delete_link.assert_called_once_with(link_id="10000")
    assert create_result.data == {
        "status": "created",
        "link_type": "Blocks",
        "outward_issue": "PROJ-1",
        "inward_issue": "PROJ-2",
    }
    assert delete_result.data == {"status": "deleted", "link_id": "10000"}
