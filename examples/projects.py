"""Example: Projects API usage."""

import os

from jira2py import JiraAPI


def search_all_projects() -> None:
    """Search all projects."""
    jira = JiraAPI()
    result = jira.projects.search_projects()
    for project in result["values"]:
        print(f"{project['key']}: {project['name']}")


def search_by_query() -> None:
    """Search projects by name."""
    jira = JiraAPI()
    result = jira.projects.search_projects(query="Service")
    print(f"Found {result['total']} projects matching 'Service'")


def search_by_keys() -> None:
    """Search projects by keys."""
    jira = JiraAPI()
    result = jira.projects.search_projects(keys=["PROJ", "TEST"])
    for project in result["values"]:
        print(f"{project['key']}: {project['name']}")


def search_with_expand() -> None:
    """Search projects with expanded properties."""
    jira = JiraAPI()
    result = jira.projects.search_projects(expand="description,lead")
    for project in result["values"]:
        print(f"{project['key']}: {project.get('description', 'No description')}")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    search_all_projects()
    search_by_query()
    search_by_keys()
    search_with_expand()
