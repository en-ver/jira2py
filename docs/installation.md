# Installation

## Requirements

- Python 3.11 or later
- A Jira Cloud instance with API access
- A Jira API token ([create one here](https://id.atlassian.com/manage-profile/security/api-tokens))

## Installation

=== "pip"

    ```bash
    pip install jira2py
    ```

=== "uv"

    ```bash
    uv add jira2py
    ```

## Authentication

jira2py uses [Jira API tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/) with HTTP Basic authentication. The quickest way to get started is to set environment variables:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

```python
from jira2py import JiraAPI

jira = JiraAPI()  # credentials loaded from environment
```

You can also pass credentials explicitly, or mix both approaches. See [Configuration](guide/configuration.md) for the full details on credential resolution, validation, and precedence rules.

## Your First Script

Here's a complete working example that fetches an issue, searches with JQL, and creates a new issue:

```python
from jira2py import JiraAPI, JiraNotFoundError

jira = JiraAPI()

# Fetch a single issue
issue = jira.issues.get_issue("PROJ-123", fields="summary,status,assignee")
print(f"{issue['key']}: {issue['fields']['summary']}")
print(f"  Status: {issue['fields']['status']['name']}")

# Search with JQL
results = jira.search.enhanced_search(
    "project = PROJ AND status = 'In Progress' ORDER BY updated DESC",
    fields=["summary", "status", "assignee"],
    max_results=10,
)
print(f"\nFound {results['total']} issues in progress:")
for item in results["issues"]:
    print(f"  {item['key']}: {item['fields']['summary']}")

# Create a new issue
new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "Created with jira2py",
    "description": {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "This issue was created via the API."}
                ],
            }
        ],
    },
})
print(f"\nCreated issue: {new_issue['key']}")
```

!!! tip "Working with Atlassian Document Format (ADF)"
The `description` and comment `body` fields use Jira's
[Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/),
which can be verbose to build by hand. Consider using a converter library
to generate ADF from Markdown or other formats. For example:

    - [marklassian](https://pypi.org/project/marklassian/) — Markdown to ADF
    - [pyadf](https://pypi.org/project/pyadf/) — ADF to Markdown

    Several other Python packages are available on PyPI for ADF conversion as well.

```python
# Handle errors gracefully

try:
    jira.issues.get_issue("NONEXISTENT-999")
except JiraNotFoundError:
    print("\nIssue not found (as expected)")
```

## What's Next

- [Configuration](guide/configuration.md) — Retry settings, timeouts, and credential details
- [Error Handling](guide/error-handling.md) — Working with the exception hierarchy
- [Rate Limiting](guide/rate-limiting.md) — How automatic retry works
- [API Reference](api/index.md) — All available endpoints and their parameters
