# JiraAPI

The main entry point for all Jira operations.

## Constructor

```python
from jira2py import JiraAPI

jira = JiraAPI(
    url: str | None = None,
    username: str | None = None,
    api_token: str | None = None,
    max_retries: int = 4,
    max_retry_delay: float = 30.0,
)
```

| Parameter | Default | Description |
|---|---|---|
| `url` | `None` | Jira instance URL. Falls back to `JIRA_URL` env var. |
| `username` | `None` | Atlassian account email. Falls back to `JIRA_USER` env var. |
| `api_token` | `None` | API token. Falls back to `JIRA_API_TOKEN` env var. |
| `max_retries` | `4` | Max retry attempts on HTTP 429. |
| `max_retry_delay` | `30.0` | Max delay between retries in seconds. |

See [Configuration](../guide/configuration.md) for credential resolution and [Rate Limiting](../guide/rate-limiting.md) for retry behavior.

## Properties

| Property | Type | Description |
|---|---|---|
| `issues` | [`Issues`](issues.md) | Issue operations |
| `search` | [`IssueSearch`](issue-search.md) | JQL search |
| `comments` | [`IssueComments`](issue-comments.md) | Issue comments |
| `fields` | [`IssueFields`](issue-fields.md) | System and custom fields |
| `issue_links` | [`IssueLinks`](issue-links.md) | Issue link operations |
| `projects` | [`Projects`](projects.md) | Project search |
| `attachments` | [`Attachments`](attachments.md) | Attachment metadata |
| `users` | [`Users`](users.md) | User search |

## Usage

```python
from jira2py import JiraAPI

jira = JiraAPI()

# Access any module through the facade
issue = jira.issues.get_issue("PROJ-123")
results = jira.search.enhanced_search("project = PROJ")
fields = jira.fields.get_fields()
projects = jira.projects.search_projects()
```
