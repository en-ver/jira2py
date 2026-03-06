"""Example: Issue Fields API usage."""

import os

from jira2py import JiraAPI


def get_fields() -> None:
    """Get all Jira fields."""
    jira = JiraAPI()
    fields = jira.fields.get_fields()
    print(f"Total fields: {len(fields)}")

    custom_fields = [f for f in fields if f.get("custom")]
    print(f"Custom fields: {len(custom_fields)}")

    for field in custom_fields[:5]:
        print(f"  {field['id']}: {field['name']}")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    get_fields()
