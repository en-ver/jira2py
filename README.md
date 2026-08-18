# jira2py

[![PyPI version](https://img.shields.io/pypi/v/jira2py.svg)](https://pypi.org/project/jira2py/)
[![Python versions](https://img.shields.io/pypi/pyversions/jira2py.svg)](https://pypi.org/project/jira2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A type-safe Python client for the [Jira Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/). Use it to read and search issues, create and edit issues, transition workflows, and work with comments, attachments, links, worklogs, projects, metadata, users, and saved filters.

## Scope

`jira2py` supports **Jira Cloud** and Python **3.11+**. It does not support Jira Server or Data Center, board/sprint/epic workflows, issue deletion or archiving, or a dedicated issue-assignment API.

## Install

```bash
pip install jira2py
```

## Authenticate safely

Create an [Atlassian API token](https://id.atlassian.com/manage-profile/security/api-tokens), then provide your Cloud URL, Atlassian account email, and token. Without `credentials_file`, each credential uses a non-empty explicit `url`, `username`, or `api_token` argument, then its `JIRA_URL`, `JIRA_USER`, or `JIRA_API_TOKEN` environment variable.

When you supply `credentials_file`, jira2py first loads and validates it as a complete set: the JSON must contain non-empty `url`, `username`, and `api_token` values. A partial file cannot be completed from explicit arguments or environment variables; after validation, non-empty explicit arguments override their matching file values.

There is no default credentials-file path. Keep tokens out of source control, logs, and error reports; use environment variables or a protected local JSON file instead.

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

```json
{
  "url": "https://your-domain.atlassian.net",
  "username": "your-email@example.com",
  "api_token": "your-api-token"
}
```

Pass the JSON file only when needed:

```python
from jira2py import JiraAPI

jira = JiraAPI(credentials_file="./jira-credentials.json")
```

## Choose an API layer

- **`JiraAPI`** is the low-level, endpoint-oriented interface. Operations return parsed Jira JSON-like data when available; downloads return bytes and operations without a response body return `None`.
- **`JiraHelpers`** provides grouped workflows and readable `HelperResult` values, with optional structured data, for common tasks.

Use `JiraAPI` when you want direct REST payloads and endpoint control:

```python
from jira2py import JiraAPI

jira = JiraAPI()
issue = jira.issues.get_issue("PROJECT-123")
results = jira.search.enhanced_search("project = PROJECT AND status = 'In Progress'")
```

Use `JiraHelpers` when grouped, human-readable results better fit your application or automation:

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

helpers = JiraHelpers(JiraAPI())
print(helpers.issues.read("PROJECT-123").text)
print(helpers.metadata.transitions("PROJECT-123").text)
print(helpers.attachments.list("PROJECT-123").text)
```

## Documentation

- [Installation](https://jira2py.org/installation/)
- [Configuration and credential details](https://jira2py.org/guide/configuration/)
- [High-level helpers](https://jira2py.org/guide/high-level-helpers/)
- [API reference](https://jira2py.org/api/)
- [Full documentation](https://jira2py.org/)
- [Machine-readable documentation](https://jira2py.org/llms.txt) and [complete reference](https://jira2py.org/llms-full.txt)

## License

[MIT](LICENSE)
