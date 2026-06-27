---
hide:
  - navigation
---

# jira2py

A lightweight, type-safe Python client for the **Jira Cloud REST API v3**.

[![PyPI](https://img.shields.io/pypi/v/jira2py)](https://pypi.org/project/jira2py/)
[![Python](https://img.shields.io/pypi/pyversions/jira2py)](https://pypi.org/project/jira2py/)
[![License](https://img.shields.io/github/license/en-ver/jira2py)](https://github.com/en-ver/jira2py/blob/main/LICENSE)

!!! note
    jira2py is **Jira Cloud only**. It does not add Jira Server/Data Center support, board/sprint/epic workflows, issue delete/archive workflows, or a dedicated issue-assign helper/API.

## Why jira2py?

jira2py provides a clean, minimal interface to Jira Cloud. It offers two complementary layers:

- `from jira2py import JiraAPI` for the low-level REST facade
- `from jira2py.helpers import JiraHelpers` for grouped high-level workflows

### Low-level `JiraAPI`

```python
from jira2py import JiraAPI

jira = JiraAPI()
issue = jira.issues.get_issue("PROJ-123")
print(issue["fields"]["summary"])
```

### High-level `JiraHelpers`

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)

print(helpers.auth.status().text)
print(helpers.metadata.transitions("PROJ-123").text)
print(helpers.attachments.list("PROJ-123").text)
print(helpers.worklogs.list("PROJ-123").text)
print(helpers.filters.run("12345").text)
```

High-level helpers return `HelperResult` objects with readable `text` plus optional structured `data` and `raw_content`.

## Credentials

By default, `JiraAPI()` reads credentials from `JIRA_URL`, `JIRA_USER`, and `JIRA_API_TOKEN`.

You can also pass an explicit JSON credentials file path with `credentials_file="./jira-credentials.json"`.

```json
{
  "url": "https://your-domain.atlassian.net",
  "username": "your-email@example.com",
  "api_token": "your-api-token"
}
```

There is **no default credentials file path**. If you do not pass `credentials_file`, jira2py uses environment variables.

## API Coverage

| Module | Operations |
| --- | --- |
| **Issues** | Get, create, edit, transition issues; changelogs; edit metadata; create metadata |
| **Issue Search** | JQL search with pagination |
| **Issue Comments** | List, add, update, delete comments |
| **Issue Worklogs** | List, add, update, delete issue worklogs |
| **Issue Fields** | List system and custom fields |
| **Issue Links** | List issue links, list link types, create and delete links |
| **Projects** | Get, search, and list projects |
| **Attachments** | List issue attachments, read metadata, download, upload, and delete attachments |
| **Users/Auth** | Search users and get the current authenticated user |
| **Metadata** | Statuses and priorities |
| **Filters** | Search/list saved filters and resolve saved JQL for search |
| **Helpers** | High-level auth, issues, search, comments, worklogs, attachments, metadata, links, and filters workflows |

## For AI Agents & LLMs

This documentation is available in machine-readable formats:

- **[llms.txt](https://jira2py.org/llms.txt)** — documentation index
- **[llms-full.txt](https://jira2py.org/llms-full.txt)** — all pages in one file
- **[api-reference.json](api-reference.json)** — generated API schema

## Next Steps

- [Installation](installation.md)
- [Configuration](guide/configuration.md)
- [High-level Helpers](guide/high-level-helpers.md)
- [API Reference](api/index.md)
