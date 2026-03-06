"""Example: Issues API usage."""

import os

from jira2py import JiraAPI


def get_issue() -> None:
    """Get an issue with default fields."""
    jira = JiraAPI()
    issue = jira.issues.get_issue("PROJECT-123")
    print(f"Issue: {issue['key']} - {issue['fields']['summary']}")


def get_issue_with_extra_params() -> None:
    """Get an issue with extra query parameters."""
    jira = JiraAPI()
    issue = jira.issues.get_issue(
        "PROJECT-123",
        extra_params={"fields": "summary,status,assignee", "expand": "renderedFields"},
    )
    print(f"Issue: {issue['key']}")


def get_changelogs() -> None:
    """Get changelogs for an issue."""
    jira = JiraAPI()
    changelogs = jira.issues.get_changelogs("PROJECT-123")
    for log in changelogs:
        for item in log.get("items", []):
            print(
                f"  {item['field']}: {item.get('fromString')} → {item.get('toString')}"
            )


def edit_issue() -> None:
    """Edit an issue."""
    jira = JiraAPI()
    jira.issues.edit_issue(
        "PROJECT-123",
        fields={"summary": "Updated summary"},
        notify_users=False,
    )
    print("Issue updated successfully")


def edit_issue_with_return() -> None:
    """Edit an issue and return the updated issue."""
    jira = JiraAPI()
    updated = jira.issues.edit_issue(
        "PROJECT-123",
        fields={"summary": "Updated summary"},
        return_issue=True,
    )
    if updated:
        print(f"Updated: {updated['key']} - {updated['fields']['summary']}")


def edit_issue_with_extra_data() -> None:
    """Edit an issue with extra data (e.g., update block)."""
    jira = JiraAPI()
    jira.issues.edit_issue(
        "PROJECT-123",
        fields={"summary": "Updated summary"},
        extra_data={
            "update": {
                "labels": [{"add": "new-label"}],
            }
        },
    )
    print("Issue updated with extra data")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    get_issue()
    get_issue_with_extra_params()
    get_changelogs()
    edit_issue()
    edit_issue_with_return()
    edit_issue_with_extra_data()
