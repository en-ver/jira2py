# jira2py

[![PyPI version](https://img.shields.io/pypi/v/jira2py.svg)](https://pypi.org/project/jira2py/)
[![Python versions](https://img.shields.io/pypi/pyversions/jira2py.svg)](https://pypi.org/project/jira2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, type-safe Python client for the [Jira Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/).

Built for developers who want to interact with Jira programmatically without pulling in heavyweight dependencies — just two runtime dependencies (`httpx`, `tenacity`).

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

## Key Features

- **Unified API** — single `JiraAPI` entry point with access to all endpoints via `jira.issues`, `jira.search`, `jira.comments`, `jira.projects`, and more
- **Automatic rate limit handling** — retries on HTTP 429 with exponential backoff, jitter, and `Retry-After` header support
- **Performant** — persistent connections with HTTP/2, configurable timeouts
- **Structured error handling** — typed exception hierarchy (`JiraNotFoundError`, `JiraValidationError`, `JiraRateLimitError`, etc.) instead of generic errors
- **Type-safe** — full type annotations and a `py.typed` marker for downstream static analysis (PEP 561)
- **Lightweight** — two runtime dependencies: `httpx` and `tenacity`

## API Coverage

| Module             | Operations                                                           |
| ------------------ | -------------------------------------------------------------------- |
| **Issues**         | Get, create, edit issues; changelogs; edit metadata; create metadata |
| **Issue Search**   | JQL search with pagination                                           |
| **Issue Comments** | List and add comments                                                |
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
