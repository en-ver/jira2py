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


def search_fields() -> None:
    """Get one searchable field catalog page using canonical Jira IDs."""
    jira = JiraAPI()
    page = jira.fields.search_fields(
        query="points",
        field_types=["custom"],
        order_by="name",
        expand="stableId",
    )
    for field in page["values"]:
        print(f"{field['name']} (id: {field['id']})")


if __name__ == "__main__":
    # Set these environment variables before running:
    # JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN
    assert os.environ.get("JIRA_URL"), "Set JIRA_URL environment variable"

    get_fields()
    search_fields()
