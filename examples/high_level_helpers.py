"""Example: High-level JiraHelpers usage."""

import os

from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers


def build_helpers() -> JiraHelpers:
    """Create the high-level helper facade from environment-based credentials."""
    return JiraHelpers(JiraAPI())


def read_issue(issue_key: str) -> None:
    """Read an issue with formatted helper output."""
    helpers = build_helpers()
    result = helpers.issues.read(issue_key)
    print(result.text)


def search_issues(jql: str) -> None:
    """Search issues with the grouped search helper."""
    helpers = build_helpers()
    result = helpers.search.issues(jql)
    print(result.text)


def list_comments(issue_key: str) -> None:
    """List comments with the grouped comments helper."""
    helpers = build_helpers()
    result = helpers.comments.list(issue_key)
    print(result.text)


def report_worklogs(jql: str, start_date: str, end_date: str) -> None:
    """Build a worklog report."""
    helpers = build_helpers()
    result = helpers.worklogs.report(
        start_date=start_date,
        end_date=end_date,
        jql=jql,
    )
    print(result.text)


def plan_attachment_download(attachment_id: str) -> None:
    """Plan an attachment download destination."""
    helpers = build_helpers()
    result = helpers.attachments.plan_download(
        attachment_id,
        output_path="downloads/",
    )
    print(result.text)
    if result.data:
        print(f"Planned file: {result.data.output_file}")


def show_metadata(project_key: str, issue_type: str, issue_key: str) -> None:
    """Inspect high-level metadata helpers."""
    helpers = build_helpers()
    print(helpers.metadata.issue_types(project_key).text)
    print(helpers.metadata.create_fields(project_key, issue_type).text)
    print(helpers.metadata.edit_fields(issue_key).text)
    print(helpers.metadata.projects(project_key).text)
    print(helpers.metadata.users("teammate@example.com").text)


def show_link_types() -> None:
    """List configured issue link types."""
    helpers = build_helpers()
    result = helpers.links.types()
    print(result.text)


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USER, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    issue_key = "PROJECT-123"
    read_issue(issue_key)
    search_issues("project = PROJECT ORDER BY updated DESC")
    list_comments(issue_key)
    report_worklogs("project = PROJECT", "2026-01-01", "2026-01-31")
    plan_attachment_download("10001")
    show_metadata("PROJECT", "Task", issue_key)
    show_link_types()
