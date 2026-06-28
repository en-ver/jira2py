# API Reference

jira2py exposes two complementary **Jira Cloud** layers:

- `from jira2py import JiraAPI` — the low-level Jira REST facade
- `from jira2py.helpers import JiraHelpers` — the high-level workflow facade

## High-level facade

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)

helpers.auth
helpers.issues
helpers.search
helpers.comments
helpers.worklogs
helpers.attachments
helpers.metadata
helpers.links
helpers.filters
```

Helper methods return `HelperResult` objects with human-readable `text` plus optional structured `data` and `raw_content`.

## Low-level facade

```python
from jira2py import JiraAPI

jira = JiraAPI()

jira.issues
jira.search
jira.comments
jira.worklogs
jira.fields
jira.issue_links
jira.projects
jira.metadata
jira.filters
jira.attachments
jira.users
```

## Modules

| Module | Property | Description |
| --- | --- | --- |
| [High-level Helpers](helpers.md) | `helpers.<group>` | Grouped helper facade returning `HelperResult` |
| [JiraAPI](jira-api.md) | — | Entry point and low-level facade |
| [Issues](issues.md) | `jira.issues` | Create, read, edit, and transition issues |
| [Issue Search](issue-search.md) | `jira.search` | Search issues with JQL |
| [Issue Comments](issue-comments.md) | `jira.comments` | List, add, update, and delete comments |
| [Issue Worklogs](issue-worklogs.md) | `jira.worklogs` | List, add, update, and delete issue worklogs |
| [Issue Fields](issue-fields.md) | `jira.fields` | List system and custom fields |
| [Issue Links](issue-links.md) | `jira.issue_links` | List issue links and link types; create and delete links |
| [Projects](projects.md) | `jira.projects` | Get, search, and list projects |
| [Metadata](metadata.md) | `jira.metadata` | Statuses and priorities |
| [Filters](filters.md) | `jira.filters` | Search saved filters and fetch saved filter JQL |
| [Attachments](attachments.md) | `jira.attachments` | List, read, download, upload, and delete attachments |
| [Users](users.md) | `jira.users` | Search users and get the current user |
| [Exceptions](exceptions.md) | — | Exception hierarchy |

## Conventions

### `extra_params` and `extra_data`

Most methods accept:

- **`extra_params`** — extra query parameters merged into the request URL
- **`extra_data`** — extra request-body fields merged into the payload

### Return types

- Low-level `JiraAPI` methods return parsed Jira REST response bodies (`dict`, `list`, or `None`)
- High-level helpers return [`HelperResult`](helpers.md#helperresult)
