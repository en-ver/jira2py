"""Example: High-level JiraHelpers usage."""

import os

from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers, format_issue


def build_helpers() -> JiraHelpers:
    """Create the high-level helper facade from environment-based credentials."""
    return JiraHelpers(JiraAPI())


def read_and_format_issue(issue_key: str) -> None:
    """Retrieve a selected issue projection and format it without another read."""
    api = JiraAPI()
    issue = api.issues.get_issue(
        issue_key,
        fields=["summary", "status", "description"],
    )
    print(
        format_issue(issue, browse_url=f"{api.credentials.url}/browse/{issue['key']}")
    )


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


def list_changelogs(issue_key: str) -> None:
    """Retrieve the complete changelog history, then locally filter by UTC time."""
    helpers = build_helpers()
    result = helpers.changelogs.list(
        issue_key,
        created_at_or_after="2026-01-01T00:00:00Z",
        created_before="2026-02-01T00:00:00Z",
    )
    print(result.text)


def list_changelogs_by_ids(issue_key: str) -> None:
    """Retrieve known changelog histories with one POST request."""
    helpers = build_helpers()
    print(helpers.changelogs.list_by_ids(issue_key, [10001, 10002]).text)


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
    read_and_format_issue(issue_key)
    search_issues("project = PROJECT ORDER BY updated DESC")
    list_comments(issue_key)
    list_changelogs(issue_key)
    list_changelogs_by_ids(issue_key)
    report_worklogs("project = PROJECT", "2026-01-01", "2026-01-31")
    plan_attachment_download("10001")
    show_metadata("PROJECT", "Task", issue_key)
    show_link_types()
