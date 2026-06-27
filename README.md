# jira2py

[![PyPI version](https://img.shields.io/pypi/v/jira2py.svg)](https://pypi.org/project/jira2py/)
[![Python versions](https://img.shields.io/pypi/pyversions/jira2py.svg)](https://pypi.org/project/jira2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, type-safe Python client for the [Jira Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/).

`jira2py` is **Jira Cloud only**. It does not add Jira Server/Data Center support, board/sprint/epic workflows, issue delete/archive workflows, or a dedicated issue-assign helper/API.

## Installation

```bash
pip install jira2py
```

## Quick Start

```python
from jira2py import JiraAPI

jira = JiraAPI(
    url="https://your-domain.atlassian.net",
    username="your-email@example.com",
    api_token="your-api-token",
)

issue = jira.issues.get_issue("PROJECT-123")
results = jira.search.enhanced_search("project = PROJECT AND status = 'In Progress'")
```

By default, `JiraAPI()` loads credentials from environment variables:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

```python
jira = JiraAPI()
```

You can also pass an explicit JSON credentials file path. There is **no default credentials file path**.

```json
{
  "url": "https://your-domain.atlassian.net",
  "username": "your-email@example.com",
  "api_token": "your-api-token"
}
```

```python
jira = JiraAPI(credentials_file="./jira-credentials.json")
```

When `credentials_file` is provided, jira2py loads that file. Explicit `url`, `username`, and `api_token` arguments still override file values.

## Choose Your API Layer

`jira2py` has two complementary layers:

- **Low-level `JiraAPI`** — endpoint-oriented methods that return Jira REST JSON shapes directly.
- **High-level `JiraHelpers`** — grouped workflows that return readable `HelperResult` objects with optional structured data.

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)

print(helpers.auth.status().text)
print(helpers.auth.me().text)
print(helpers.metadata.transitions("PROJECT-123").text)
print(helpers.comments.update("PROJECT-123", "10001", "Updated comment").text)
print(helpers.attachments.list("PROJECT-123").text)
print(helpers.links.list("PROJECT-123").text)
print(helpers.worklogs.list("PROJECT-123").text)
print(helpers.metadata.project("PROJECT").text)
print(helpers.metadata.statuses().text)
print(helpers.metadata.priorities().text)
print(helpers.filters.search("Team").text)
print(helpers.filters.run("12345", fields=["summary", "status"]).text)
```

Helper methods cover:

- auth status and current user (`helpers.auth.status()`, `helpers.auth.me()`)
- issue read/create/edit and workflow transitions
- comment list/add/update/delete
- attachment list/read/plan/download/upload/delete
- issue-link list/types/create/delete
- worklog list/add/update/delete/report
- project lookup, project search, transitions, statuses, priorities, users, and field metadata
- saved filter list/search and filter-run via resolved JQL

`filter-run` is exposed as a helper workflow: it resolves the saved filter JQL and returns the same output shape as normal issue search.

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
| **Users** | Search users and get the current authenticated user |
| **Metadata** | Statuses and priorities |
| **Filters** | Search/list saved filters and resolve filter JQL |
| **Helpers** | High-level auth, issues, search, comments, worklogs, attachments, metadata, links, and filters workflows |

## Documentation

Full documentation is available at **[jira2py.org](https://jira2py.org)**.

Machine-readable documentation for AI agents and LLMs:

- [llms.txt](https://jira2py.org/llms.txt)
- [llms-full.txt](https://jira2py.org/llms-full.txt)
- [api-reference.json](https://jira2py.org/api-reference.json)

## License

[MIT](LICENSE)
