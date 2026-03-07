"""Example: Issue Comments API usage."""

import os

from jira2py import JiraAPI


def get_comments() -> None:
    """Get comments for an issue."""
    jira = JiraAPI()
    result = jira.comments.get_comments("PROJECT-123")
    print(f"Total comments: {result['total']}")
    for comment in result["comments"]:
        print(f"  Comment {comment['id']}")


def get_comments_with_expand() -> None:
    """Get comments with rendered body."""
    jira = JiraAPI()
    result = jira.comments.get_comments(
        "PROJECT-123",
        expand="renderedBody",
        order_by="-created",
        max_results=10,
    )
    for comment in result["comments"]:
        print(f"  Comment {comment['id']}")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    get_comments()
    get_comments_with_expand()
