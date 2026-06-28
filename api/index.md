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

| Module                                                            | Property           | Description                                              |
| ----------------------------------------------------------------- | ------------------ | -------------------------------------------------------- |
| [High-level Helpers](https://jira2py.org/api/helpers/index.md)    | `helpers.<group>`  | Grouped helper facade returning `HelperResult`           |
| [JiraAPI](https://jira2py.org/api/jira-api/index.md)              | —                  | Entry point and low-level facade                         |
| [Issues](https://jira2py.org/api/issues/index.md)                 | `jira.issues`      | Create, read, edit, and transition issues                |
| [Issue Search](https://jira2py.org/api/issue-search/index.md)     | `jira.search`      | Search issues with JQL                                   |
| [Issue Comments](https://jira2py.org/api/issue-comments/index.md) | `jira.comments`    | List, add, update, and delete comments                   |
| [Issue Worklogs](https://jira2py.org/api/issue-worklogs/index.md) | `jira.worklogs`    | List, add, update, and delete issue worklogs             |
| [Issue Fields](https://jira2py.org/api/issue-fields/index.md)     | `jira.fields`      | List system and custom fields                            |
| [Issue Links](https://jira2py.org/api/issue-links/index.md)       | `jira.issue_links` | List issue links and link types; create and delete links |
| [Projects](https://jira2py.org/api/projects/index.md)             | `jira.projects`    | Get, search, and list projects                           |
| [Metadata](https://jira2py.org/api/metadata/index.md)             | `jira.metadata`    | Statuses and priorities                                  |
| [Filters](https://jira2py.org/api/filters/index.md)               | `jira.filters`     | Search saved filters and fetch saved filter JQL          |
| [Attachments](https://jira2py.org/api/attachments/index.md)       | `jira.attachments` | List, read, download, upload, and delete attachments     |
| [Users](https://jira2py.org/api/users/index.md)                   | `jira.users`       | Search users and get the current user                    |
| [Exceptions](https://jira2py.org/api/exceptions/index.md)         | —                  | Exception hierarchy                                      |

## Conventions

### `extra_params` and `extra_data`

Most methods accept:

- **`extra_params`** — extra query parameters merged into the request URL
- **`extra_data`** — extra request-body fields merged into the payload

### Return types

- Low-level `JiraAPI` methods return parsed Jira REST response bodies (`dict`, `list`, or `None`)
- High-level helpers return [`HelperResult`](https://jira2py.org/api/helpers/#helperresult)
