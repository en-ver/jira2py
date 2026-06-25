---
hide:
  - navigation
---

# jira2py

A lightweight, type-safe Python client for the Jira REST API.

[![PyPI](https://img.shields.io/pypi/v/jira2py)](https://pypi.org/project/jira2py/)
[![Python](https://img.shields.io/pypi/pyversions/jira2py)](https://pypi.org/project/jira2py/)
[![License](https://img.shields.io/github/license/en-ver/jira2py)](https://github.com/en-ver/jira2py/blob/main/LICENSE)

---

## Why jira2py?

jira2py provides a clean, minimal interface to the Jira Cloud REST API v3. It's built for developers who want to interact with Jira programmatically without pulling in heavyweight dependencies.

```python
from jira2py import JiraAPI

jira = JiraAPI()

issue = jira.issues.get_issue("PROJ-123")
print(issue["fields"]["summary"])
```

## Key Features

- **Unified API** — Single `JiraAPI` entry point with access to all endpoints via `jira.issues`, `jira.search`, `jira.comments`, `jira.projects`, and more
- **Automatic rate limit handling** — Retries on HTTP 429 with exponential backoff, jitter, and `Retry-After` header support
- **Performant** — Persistent connections with HTTP/2, configurable timeouts
- **Structured error handling** — Typed exception hierarchy (`JiraNotFoundError`, `JiraValidationError`, `JiraRateLimitError`, etc.) instead of generic errors
- **Type-safe** — Full type annotations and a `py.typed` marker for downstream static analysis
- **Lightweight** — Minimal runtime dependencies

## API Coverage

| Module             | Operations                                                           |
| ------------------ | -------------------------------------------------------------------- |
| **Issues**         | Get, create, edit issues; changelogs; edit metadata; create metadata |
| **Issue Search**   | JQL search with pagination                                           |
| **Issue Comments** | List and add comments                                                |
| **Issue Worklogs** | Retrieve issue worklogs as raw Jira pages                            |
| **Issue Fields**   | List system and custom fields                                        |
| **Issue Links**    | List link types, create and delete links                             |
| **Projects**       | Search and list projects                                             |
| **Attachments**    | Get attachment metadata                                              |
| **Users**          | Search users by name or email                                        |

## For AI Agents & LLMs

This documentation is available in machine-readable formats:

- **[llms.txt](llms.txt)** — documentation index with links to Markdown versions of each page
- **[llms-full.txt](llms-full.txt)** — all documentation pages expanded into a single file
- **[api-reference.json](api-reference.json)** — full API schema with signatures, types, and docstrings, generated from source with [griffe](https://github.com/mkdocstrings/griffe)

These files are regenerated on every release and always reflect the latest source code.

## Quick Start

Install from PyPI:

```bash
pip install jira2py
```

Credentials can be provided explicitly or loaded from environment variables (`JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`). See [Configuration](guide/configuration.md) for details.

```python
from jira2py import JiraAPI

jira = JiraAPI()  # from environment variables
# or: jira = JiraAPI(url="...", username="...", api_token="...")

# Search issues
results = jira.search.enhanced_search(
    "project = PROJ ORDER BY created DESC"
)
for issue in results["issues"]:
    print(issue["key"], issue["fields"]["summary"])

# Create an issue
new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "New task from jira2py",
})
print(f"Created {new_issue['key']}")
```

See the [Installation](installation.md) guide for detailed setup instructions.
