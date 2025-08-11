#!/usr/bin/env python3
"""
Script to fetch real Jira data and anonymize it for use as test fixtures.

This script connects to a real Jira instance, fetches sample data,
and anonymizes it to create realistic but safe test fixtures.

Usage:
    python scripts/fetch_test_data.py

Requirements:
    - JIRA_URL, JIRA_USER, and JIRA_API_TOKEN environment variables set
    - Or .env file with these variables
"""

import json
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv

from jira2py.issue_comments import IssueComments
from jira2py.issue_fields import IssueFields
from jira2py.issue_search import IssueSearch
from jira2py.issues import Issues


def anonymize_text(text: str) -> str:
    """Anonymize text by replacing sensitive information."""
    if not text:
        return text

    # Replace common sensitive patterns
    text = text.replace(os.getenv("JIRA_USER", ""), "test@example.com")

    # Replace URLs
    import re

    text = re.sub(r"https?://[^\s]+", "https://example.com", text)

    # Replace email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "test@example.com", text
    )

    return text


def anonymize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize an issue object."""
    if not issue:
        return issue

    # Create a copy to avoid modifying the original
    anonymized = issue.copy()

    # Anonymize key and ID
    if "key" in anonymized:
        anonymized["key"] = "TEST-" + "".join(
            filter(str.isdigit, anonymized["key"]) or "123"
        )

    if "id" in anonymized:
        anonymized["id"] = str(
            int(anonymized["id"]) % 100000 + 10000
        )  # Keep it numeric but different

    # Anonymize fields
    if "fields" in anonymized and isinstance(anonymized["fields"], dict):
        fields = anonymized["fields"]
        if "summary" in fields:
            fields["summary"] = anonymize_text(fields["summary"])
        if "description" in fields:
            fields["description"] = anonymize_text(fields["description"])

    return anonymized


def anonymize_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymize a comment object."""
    if not comment:
        return comment

    # Create a copy to avoid modifying the original
    anonymized = comment.copy()

    # Anonymize author
    if "author" in anonymized and isinstance(anonymized["author"], dict):
        author = anonymized["author"]
        if "name" in author:
            author["name"] = "testuser"
        if "emailAddress" in author:
            author["emailAddress"] = "test@example.com"

    # Anonymize body
    if "body" in anonymized:
        anonymized["body"] = anonymize_text(anonymized["body"])

    return anonymized


def fetch_and_save_sample_data() -> bool:
    """Fetch sample data from Jira and save anonymized versions."""
    print("Loading environment variables...")
    load_dotenv()

    # Check required environment variables
    required_vars = ["JIRA_URL", "JIRA_USER", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Using sample data from tests/fixtures/ instead.")
        return True

    try:
        print("Connecting to Jira...")
        issues_client = Issues()
        search_client = IssueSearch()
        fields_client = IssueFields()
        comments_client = IssueComments()

        # Fetch issue fields
        print("Fetching issue fields...")
        fields = fields_client.get_fields()
        # Save anonymized fields
        with open("tests/fixtures/fields.json", "w") as f:
            json.dump(fields[:10], f, indent=2)  # Save first 10 fields

        # Search for some issues
        print("Searching for issues...")
        search_result = search_client.enhanced_search(
            jql="project IS NOT EMPTY ORDER BY created DESC", max_results=5
        )

        # Save anonymized search results
        anonymized_issues = [
            anonymize_issue(issue) for issue in search_result.get("issues", [])
        ]
        search_result["issues"] = anonymized_issues

        with open("tests/fixtures/search_results.json", "w") as f:
            json.dump(search_result, f, indent=2)

        # If we found issues, fetch details for one of them
        if search_result.get("issues"):
            issue_key = search_result["issues"][0]["key"]
            print(f"Fetching details for issue {issue_key}...")

            # Get issue details
            issue_details = issues_client.get_issue(issue_key)
            anonymized_issue_details = anonymize_issue(issue_details)

            with open("tests/fixtures/issue_details.json", "w") as f:
                json.dump(anonymized_issue_details, f, indent=2)

            # Get issue changelogs
            print(f"Fetching changelogs for issue {issue_key}...")
            changelogs = issues_client.get_changelogs(issue_key)

            with open("tests/fixtures/changelogs.json", "w") as f:
                json.dump(changelogs, f, indent=2)

            # Get issue comments
            print(f"Fetching comments for issue {issue_key}...")
            comments = comments_client.get_comments(issue_key)
            # Anonymize comments
            if "comments" in comments:
                comments["comments"] = [
                    anonymize_comment(comment) for comment in comments["comments"]
                ]

            with open("tests/fixtures/comments.json", "w") as f:
                json.dump(comments, f, indent=2)

        print("Successfully fetched and anonymized sample data!")
        print("Data saved to tests/fixtures/")
        return True

    except Exception as e:
        print(f"Error fetching data: {e}")
        print("Using sample data from tests/fixtures/ instead.")
        return True


if __name__ == "__main__":
    # Create fixtures directory if it doesn't exist
    os.makedirs("tests/fixtures", exist_ok=True)

    success = fetch_and_save_sample_data()
    sys.exit(0 if success else 1)
