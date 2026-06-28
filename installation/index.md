# Installation

## Requirements

- Python 3.11 or later
- A Jira Cloud instance with API access
- A Jira API token ([create one here](https://id.atlassian.com/manage-profile/security/api-tokens))

Note

jira2py supports **Jira Cloud only**.

## Installation

```bash
pip install jira2py
```

```bash
uv add jira2py
```

## Authentication

jira2py uses Jira API tokens with HTTP Basic authentication.

### Default: environment variables

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

```python
from jira2py import JiraAPI

jira = JiraAPI()  # credentials loaded from environment
```

### Optional: explicit credentials file

If you pass `credentials_file`, jira2py loads that explicit JSON file. There is **no default credentials file path**.

```json
{
  "url": "https://your-domain.atlassian.net",
  "username": "your-email@example.com",
  "api_token": "your-api-token"
}
```

```python
from jira2py import JiraAPI

jira = JiraAPI(credentials_file="./jira-credentials.json")
```

Explicit constructor arguments still override values loaded from the file.

See [Configuration](https://jira2py.org/guide/configuration/index.md) for credential resolution and validation details.

## Your First Script

```python
from jira2py import JiraAPI, JiraNotFoundError

jira = JiraAPI()

issue = jira.issues.get_issue("PROJ-123", fields="summary,status,assignee")
print(f"{issue['key']}: {issue['fields']['summary']}")
print(f"  Status: {issue['fields']['status']['name']}")

results = jira.search.enhanced_search(
    "project = PROJ AND status = 'In Progress' ORDER BY updated DESC",
    fields=["summary", "status", "assignee"],
    max_results=10,
)
print(f"\nFound {results['total']} issues in progress:")
for item in results["issues"]:
    print(f"  {item['key']}: {item['fields']['summary']}")

new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "Created with jira2py",
})
print(f"\nCreated issue: {new_issue['key']}")

print(jira.users.get_current_user()["displayName"])
```

Working with Atlassian Document Format (ADF)

The `description`, comment `body`, and worklog `comment` fields use Jira's [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/). Libraries such as [marklassian](https://pypi.org/project/marklassian/) can help convert Markdown to ADF.

```python
try:
    jira.issues.get_issue("NONEXISTENT-999")
except JiraNotFoundError:
    print("\nIssue not found (as expected)")
```

## What's Next

- [Configuration](https://jira2py.org/guide/configuration/index.md)
- [High-level Helpers](https://jira2py.org/guide/high-level-helpers/index.md)
- [Error Handling](https://jira2py.org/guide/error-handling/index.md)
- [Rate Limiting](https://jira2py.org/guide/rate-limiting/index.md)
- [API Reference](https://jira2py.org/api/index.md)
