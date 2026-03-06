"""Example: Issue Search API usage."""

import os

from jira2py import JiraAPI


def basic_search() -> None:
    """Basic JQL search."""
    jira = JiraAPI()
    result = jira.search.enhanced_search("project = PROJECT AND status = 'Open'")
    print(f"Found {result['total']} issues")
    for issue in result["issues"]:
        print(f"  {issue['key']}: {issue['fields']['summary']}")


def search_with_fields() -> None:
    """Search with specific fields."""
    jira = JiraAPI()
    result = jira.search.enhanced_search(
        jql="project = PROJECT",
        fields=["summary", "status", "assignee"],
        max_results=10,
    )
    for issue in result["issues"]:
        print(f"  {issue['key']}: {issue['fields']['summary']}")


def search_with_extra_params() -> None:
    """Search with extra parameters."""
    jira = JiraAPI()
    result = jira.search.enhanced_search(
        jql="project = PROJECT",
        extra_data={"expand": ["renderedFields"]},
    )
    print(f"Found {result['total']} issues")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    basic_search()
    search_with_fields()
    search_with_extra_params()
