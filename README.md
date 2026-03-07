# jira2py

[![PyPI version](https://img.shields.io/pypi/v/jira2py.svg)](https://pypi.org/project/jira2py/)
[![Python versions](https://img.shields.io/pypi/pyversions/jira2py.svg)](https://pypi.org/project/jira2py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**jira2py** is a Python package designed for seamless integration with JIRA API. It provides an intuitive and modular approach to managing issues, searching for data, handling fields, and interacting with JIRA. The package is built on top of the official Jira API and simply wraps the API calls into a Pythonic interface.

---

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

# Get project list
projects = jira.projects.search_projects()
```

### Environment Variables

Credentials can be loaded automatically from environment variables:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_USER="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

```python
from jira2py import JiraAPI

jira = JiraAPI()  # Credentials loaded from environment
```

## Features

- **Issue Management**: Retrieve, create, edit, and delete JIRA issues
- **JQL Search**: Search for issues using JIRA Query Language
- **Field Management**: Fetch metadata about JIRA fields
- **Comments**: Add and retrieve issue comments
- **Projects**: Search and list projects
- **Attachments**: Access issue attachments
- **Issue Links**: Create and manage issue links
- **User Search**: Find JIRA users
- **Automatic Rate Limit Handling**: Retries on HTTP 429 with exponential backoff, respects `Retry-After` header. Configurable via `max_retries` (default: 4) and `max_retry_delay` (default: 30s). Disable with `max_retries=0`.
- **Type Safety**: Full type hints with `py.typed` marker (PEP 561)

## Documentation

Full documentation is available at [jira2py.org](https://jira2py.org).

---

## Development

This project includes a Makefile for common development tasks:

