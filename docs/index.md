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

jira2py provides a clean, minimal interface to the Jira Cloud REST API v3. It now offers two complementary layers:

- `from jira2py import JiraAPI` for the unchanged low-level REST facade
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

issue = helpers.issues.read("PROJ-123")
search = helpers.search.issues("project = PROJ ORDER BY updated DESC")
comments = helpers.comments.list("PROJ-123")
worklogs = helpers.worklogs.report(
    start_date="2026-01-01",
    end_date="2026-01-31",
    jql="project = PROJ",
)
attachment = helpers.attachments.plan_download("10001", output_path="downloads/")
metadata = helpers.metadata.issue_types("PROJ")
links = helpers.links.types()

print(issue.text)
print(search.text)
print(comments.text)
print(worklogs.text)
print(attachment.text)
print(metadata.text)
print(links.text)
```

High-level helper methods return `HelperResult` objects and raise helper-layer errors such as `JiraHelperValidationError` and `JiraHelperOperationError`.

## Key Features

- **Two API layers** — Unchanged low-level `JiraAPI` plus grouped high-level `jira2py.helpers.JiraHelpers`
- **Unified low-level facade** — Single `JiraAPI` entry point with access to all endpoints via `jira.issues`, `jira.search`, `jira.comments`, `jira.projects`, and more
- **Automatic rate limit handling** — Retries on HTTP 429 with exponential backoff, jitter, and `Retry-After` header support
- **Performant** — Persistent connections with HTTP/2, configurable timeouts
- **Structured error handling** — Typed exception hierarchy (`JiraNotFoundError`, `JiraValidationError`, `JiraRateLimitError`, etc.) instead of generic errors
- **Type-safe** — Full type annotations and a `py.typed` marker for downstream static analysis
- **Lightweight** — Focused runtime dependencies without a heavyweight Jira SDK

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

- **[llms.txt](https://jira2py.org/llms.txt)** — documentation index with links to Markdown versions of each page
- **[llms-full.txt](https://jira2py.org/llms-full.txt)** — all documentation pages expanded into a single file
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

Private helper internals such as `jira2py.helpers._adf` and `jira2py.helpers._text` are not part of the supported public API.

See the [Installation](installation.md) guide for detailed setup instructions, the [High-level Helpers](guide/high-level-helpers.md) guide for workflow examples, and the API reference for both layers.
