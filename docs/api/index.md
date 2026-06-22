# API Reference

All Jira operations are accessed through the `JiraAPI` facade. Each API module is available as a property:

```python
from jira2py import JiraAPI

jira = JiraAPI()

jira.issues            # Issues — get, create, edit, metadata
jira.search            # Issue Search — JQL queries
jira.comments          # Issue Comments — list, add
jira.fields            # Issue Fields — list system and custom fields
jira.issue_links       # Issue Links — link types, create, delete
jira.projects          # Projects — search and list
jira.attachments       # Attachments — metadata
jira.users             # Users — search
```

## Modules

| Module | Property | Description |
|---|---|---|
| [JiraAPI](jira-api.md) | — | Entry point and facade |
| [Issues](issues.md) | `jira.issues` | Create, read, and update issues; changelogs and create/edit metadata |
| [Issue Search](issue-search.md) | `jira.search` | Search issues with JQL |
| [Issue Comments](issue-comments.md) | `jira.comments` | List and add comments |
| [Issue Fields](issue-fields.md) | `jira.fields` | List system and custom fields |
| [Issue Links](issue-links.md) | `jira.issue_links` | List link types, create and delete links |
| [Projects](projects.md) | `jira.projects` | Search and list projects |
| [Attachments](attachments.md) | `jira.attachments` | Get attachment metadata |
| [Users](users.md) | `jira.users` | Search users by name or email |
| [Exceptions](exceptions.md) | — | Exception hierarchy |

## Conventions

### `extra_params` and `extra_data`

Most methods accept two optional keyword arguments for extensibility:

- **`extra_params`** — Additional query parameters merged into the request URL. `extra_params` takes precedence over named parameters if there's a key conflict.
- **`extra_data`** — Additional fields merged into the request body. `extra_data` takes precedence over named data fields if there's a key conflict.

These allow you to use Jira REST API parameters that jira2py doesn't expose as named arguments:

```python
issue = jira.issues.get_issue(
    "PROJ-123",
    extra_params={"fieldsByKeys": True, "properties": "myProp"},
)
```

### Return types

- Methods that return data give back `dict[str, Any]` or `list[dict[str, Any]]` — the parsed JSON from the Jira REST API.
- Methods for operations with no response body (e.g., delete, create link) return `None`.
- Paginated endpoints return the full response dict including `startAt`, `maxResults`, `total`, and the results list.
