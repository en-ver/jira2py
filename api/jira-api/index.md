# JiraAPI

`JiraAPI` is the low-level entry point for Jira Cloud operations.

## Constructor

```python
from jira2py import JiraAPI

jira = JiraAPI(
    url=None,
    username=None,
    api_token=None,
    max_retries=4,
    max_retry_delay=30.0,
    credentials_file=None,
)
```

| Parameter          | Default | Description                                                                                    |
| ------------------ | ------- | ---------------------------------------------------------------------------------------------- |
| `url`              | `None`  | Jira site URL. Overrides file/env values when provided.                                        |
| `username`         | `None`  | Atlassian account email. Overrides file/env values when provided.                              |
| `api_token`        | `None`  | Jira API token. Overrides file/env values when provided.                                       |
| `max_retries`      | `4`     | Max retry attempts on HTTP 429.                                                                |
| `max_retry_delay`  | `30.0`  | Max delay between retries in seconds.                                                          |
| `credentials_file` | `None`  | Explicit path to a JSON file with `url`, `username`, and `api_token`. No default path is used. |

If `credentials_file` is omitted, jira2py falls back to `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN`.

## Properties

| Property      | Type                                                               | Description                       |
| ------------- | ------------------------------------------------------------------ | --------------------------------- |
| `issues`      | [`Issues`](https://jira2py.org/api/issues/index.md)                | Issue operations                  |
| `search`      | [`IssueSearch`](https://jira2py.org/api/issue-search/index.md)     | JQL search                        |
| `comments`    | [`IssueComments`](https://jira2py.org/api/issue-comments/index.md) | Issue comments                    |
| `worklogs`    | [`IssueWorklogs`](https://jira2py.org/api/issue-worklogs/index.md) | Issue worklogs                    |
| `fields`      | [`IssueFields`](https://jira2py.org/api/issue-fields/index.md)     | System and custom fields          |
| `issue_links` | [`IssueLinks`](https://jira2py.org/api/issue-links/index.md)       | Issue-link operations             |
| `projects`    | [`Projects`](https://jira2py.org/api/projects/index.md)            | Project lookup and search         |
| `metadata`    | [`Metadata`](https://jira2py.org/api/metadata/index.md)            | Statuses and priorities           |
| `filters`     | [`Filters`](https://jira2py.org/api/filters/index.md)              | Saved filter discovery and lookup |
| `attachments` | [`Attachments`](https://jira2py.org/api/attachments/index.md)      | Attachment operations             |
| `users`       | [`Users`](https://jira2py.org/api/users/index.md)                  | User search and current user      |

## Usage

```python
from jira2py import JiraAPI

jira = JiraAPI()

issue = jira.issues.get_issue("PROJ-123")
me = jira.users.get_current_user()
transitions = jira.issues.get_transitions("PROJ-123")
project = jira.projects.get_project("PROJ")
statuses = jira.metadata.get_statuses()
filters = jira.filters.search_filters(max_results=10)
```

See [Configuration](https://jira2py.org/guide/configuration/index.md) for credential resolution and [Rate Limiting](https://jira2py.org/guide/rate-limiting/index.md) for retry behavior.
