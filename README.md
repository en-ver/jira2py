# jira2py

[![PyPI version](https://img.shields.io/pypi/v/jira2py.svg)](https://pypi.org/project/jira2py/)
[![Python versions](https://img.shields.io/pypi/pyversions/jira2py.svg)](https://pypi.org/project/jira2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, type-safe Python client for the [Jira Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/).

Built for developers who want to interact with Jira programmatically without pulling in a heavyweight Jira SDK.

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

# Get an issue
issue = jira.issues.get_issue("PROJECT-123")

# Search with JQL
results = jira.search.enhanced_search("project = PROJECT AND status = 'In Progress'")

# Create an issue
new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJECT"},
    "issuetype": {"name": "Task"},
    "summary": "New task from jira2py",
})
```

Credentials can also be loaded automatically from environment variables (`JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`):

```python
jira = JiraAPI()  # no arguments needed
```

## Choose Your API Layer

`jira2py` now has two complementary layers:

- **Low-level `JiraAPI`** — the existing endpoint-oriented facade that returns Jira REST JSON shapes directly.
- **High-level `JiraHelpers`** — an optional workflow/helper facade built on top of `JiraAPI`.

Import helpers from `jira2py.helpers`, not top-level `jira2py`:

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)

issue = helpers.issues.read("PROJECT-123")
search = helpers.search.issues("project = PROJECT ORDER BY updated DESC")
comments = helpers.comments.list("PROJECT-123")
worklogs = helpers.worklogs.report(
    start_date="2026-01-01",
    end_date="2026-01-31",
    jql="project = PROJECT",
)
attachment = helpers.attachments.plan_download("10001", output_path="downloads/")
metadata = helpers.metadata.issue_types("PROJECT")
links = helpers.links.types()

print(issue.text)
print(search.data["issues"][0]["key"] if search.data and search.data["issues"] else "No issues")
print(comments.text)
print(worklogs.text)
print(attachment.data.output_file if attachment.data else "No plan")
print(metadata.text)
print(links.text)
```

Helper methods return `HelperResult`, which combines human-readable `text` with optional structured `data` and `raw_content`. They raise helper-layer errors such as `JiraHelperValidationError` and `JiraHelperOperationError`.

Internal converters/formatters such as `jira2py.helpers._adf` and `jira2py.helpers._text` are intentionally private implementation details, not supported public API.

See also `docs/guide/high-level-helpers.md` and `examples/high_level_helpers.py` in the repository.

## Key Features

- **Two API layers** — unchanged low-level `JiraAPI` plus optional high-level `jira2py.helpers.JiraHelpers`
- **Unified low-level facade** — single `JiraAPI` entry point with access to all endpoints via `jira.issues`, `jira.search`, `jira.comments`, `jira.projects`, and more
- **Automatic rate limit handling** — retries on HTTP 429 with exponential backoff, jitter, and `Retry-After` header support
- **Performant** — persistent connections with HTTP/2, configurable timeouts
- **Structured error handling** — typed exception hierarchy (`JiraNotFoundError`, `JiraValidationError`, `JiraRateLimitError`, etc.) instead of generic errors
- **Type-safe** — full type annotations and a `py.typed` marker for downstream static analysis (PEP 561)
- **Lightweight** — lean transport/client stack without a heavyweight Jira SDK

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

## Documentation

Full documentation is available at **[jira2py.org](https://jira2py.org)** — including installation, configuration, error handling, rate limiting, and a complete API reference.

Machine-readable documentation for AI agents and LLMs:

- [llms.txt](https://jira2py.org/llms.txt) — documentation index with links to Markdown versions of each page
- [llms-full.txt](https://jira2py.org/llms-full.txt) — all documentation pages in a single file
- [api-reference.json](https://jira2py.org/api-reference.json) — full API schema with signatures, types, and docstrings

## License

[MIT](LICENSE)
