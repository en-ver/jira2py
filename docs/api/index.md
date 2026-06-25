# API Reference

jira2py exposes two complementary layers:

- `from jira2py import JiraAPI` — the unchanged low-level Jira REST facade
- `from jira2py.helpers import JiraHelpers` — a grouped high-level workflow facade built on top of `JiraAPI`

## High-level facade

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)

helpers.issues         # Read/create/edit issue workflows
helpers.search         # JQL search workflows
helpers.comments       # Comment workflows
helpers.worklogs       # Worklog reporting workflows
helpers.attachments    # Attachment validation/planning workflows
helpers.metadata       # Issue-type/field/project/user discovery workflows
helpers.links          # Issue-link workflows
```

Helper methods return `HelperResult` objects with human-readable `text` plus optional structured `data` and `raw_content`.

## Low-level facade

```python
from jira2py import JiraAPI

jira = JiraAPI()

jira.issues            # Issues — get, create, edit, metadata
jira.search            # Issue Search — JQL queries
jira.comments          # Issue Comments — list, add
jira.worklogs          # Issue Worklogs — list worklogs for an issue
jira.fields            # Issue Fields — list system and custom fields
jira.issue_links       # Issue Links — link types, create, delete
jira.projects          # Projects — search and list
jira.attachments       # Attachments — metadata
jira.users             # Users — search
```

## Modules

| Module | Property | Description |
|---|---|---|
| [High-level Helpers](helpers.md) | `helpers.<group>` | Grouped helper facade returning `HelperResult` |
| [JiraAPI](jira-api.md) | — | Entry point and low-level facade |
| [Issues](issues.md) | `jira.issues` | Create, read, and update issues; changelogs and create/edit metadata |
| [Issue Search](issue-search.md) | `jira.search` | Search issues with JQL |
| [Issue Comments](issue-comments.md) | `jira.comments` | List and add comments |
| [Issue Worklogs](issue-worklogs.md) | `jira.worklogs` | Retrieve issue worklogs as raw Jira pages |
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

- Low-level `JiraAPI` methods return `dict[str, Any]`, `list[dict[str, Any]]`, or `None` — the parsed Jira REST API response bodies.
- High-level `JiraHelpers` methods return [`HelperResult`](helpers.md#helperresult), which combines readable `text` with optional structured `data` and `raw_content`.
- Paginated low-level endpoints return the full Jira response dict including pagination metadata.
