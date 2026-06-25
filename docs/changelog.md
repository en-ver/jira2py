# Changelog

## Unreleased

### Added

- Added `jira2py.helpers.JiraHelpers`, a grouped high-level workflow facade around the unchanged low-level `JiraAPI`.
- Added grouped helper entry points for `issues`, `search`, `comments`, `worklogs`, `attachments`, `metadata`, and `links`.
- Added `HelperResult` and helper-layer errors for readable workflow output plus structured data.

### Documentation

- Documented when to use low-level `JiraAPI` vs high-level `JiraHelpers`.
- Added high-level helper guide/API reference pages and a repository example.
- Documented that private helper internals such as `jira2py.helpers._adf` and `jira2py.helpers._text` are internal implementation details, not supported public API.

## v0.5.0

Compatibility-honest minor release for accepted caller-visible behavior changes that should not be framed as a patch-only update.

### Compatibility notes

- `extra_params` and `extra_data` override named query/body fields when the same keys are provided in both places.
- `JiraAuthenticationError` subclasses `JiraAPIError`, so broad `except JiraAPIError` handlers also catch authentication/authorization failures.
- `search.enhanced_search()` omits optional `None` values from the request body instead of sending JSON `null`.

### Documentation

- Clarified the caller-visible precedence behavior for `extra_params` and `extra_data`.
- Documented the `JiraAuthenticationError` / `JiraAPIError` hierarchy and shared API error metadata (`status_code`, `response`, and `error_messages`) when available.
- Documented that `search.enhanced_search()` omits optional `None` values from the request body.

### Tooling

- Added a reusable version bump helper plus safer release-prep and tag-push automation for the `dev -> PR -> main -> tag` release flow.

## v0.4.0

### Breaking Changes

- **New entry point** — The library is now accessed through a single `JiraAPI` facade. The previous per-class imports (`from jira2py import Issues`) have been removed. See [Installation](installation.md) for the new usage.

- **Constructor parameter names changed:**

    | v0.3.x | v0.4.0 |
    |---|---|
    | `jira_url` | `url` |
    | `jira_user` | `username` |
    | `jira_api_token` | `api_token` |

- **`raw_response` mode removed** — All methods return parsed JSON (`dict`, `list`, or `None`).

- **Method signature changes** — Several methods had parameters removed in favor of `extra_params` / `extra_data`. See [API Reference — Conventions](api/index.md#extra_params-and-extra_data) for how to pass additional parameters.

    - `get_issue()` — removed: `fields_by_keys`, `properties`, `update_history`, `fail_fast`
    - `edit_issue()` — removed: `override_screen_security`, `override_editable_flag`, `history_metadata`, `properties`, `transitions`, `update`, `additional_properties`
    - `enhanced_search()` — removed: `properties`, `fields_by_keys`, `fail_fast`, `reconcile_issues`

- **Return type changes:**

    - `edit_issue()` returns `None` on success instead of `True`. Returns `dict` when `return_issue=True`.
    - `get_changelogs()` returns the full paginated response dict instead of just the values list.

- **Error types changed** — All errors were previously raised as `ValueError`. They are now specific exception types. See [Error Handling](guide/error-handling.md).

- **Pydantic validation removed** — `@validate_call` decorators are no longer used. Type hints remain for IDE support and static analysis.

### New Features

- **Unified API facade** — Single `JiraAPI` entry point with access to all modules via properties (`jira.issues`, `jira.search`, `jira.comments`, etc.).

- **Automatic rate limit handling** — Requests that receive HTTP 429 are retried automatically with exponential backoff and `Retry-After` header support. See [Rate Limiting](guide/rate-limiting.md).

- **Structured exception hierarchy** — Typed exceptions for authentication errors, not found, validation failures, rate limits, and connection issues. See [Error Handling](guide/error-handling.md).

- **11 new API methods:**

    | Method | Description |
    |---|---|
    | `issues.create_issue()` | Create a new issue |
    | `issues.get_edit_metadata()` | Get fields available for editing |
    | `issues.get_create_issue_types()` | Get issue types for a project |
    | `issues.get_create_fields()` | Get fields for creating an issue type |
    | `comments.add_comment()` | Add a comment to an issue |
    | `issue_links.get_link_types()` | List available link types |
    | `issue_links.create_link()` | Link two issues |
    | `issue_links.delete_link()` | Delete an issue link |
    | `attachments.get_attachment_metadata()` | Get attachment metadata |
    | `projects.search_projects()` | Search and list projects |
    | `users.search_users()` | Search users by name or email |

- **HTTP/2 support** with persistent connections and configurable timeouts.

- **PEP 561 compliant** — `py.typed` marker included for downstream type checking.

### Bug Fixes

- **`get_comments()` ordering** — Fixed the `order_by` query parameter name from `orderby` to `orderBy`. The incorrect name was silently ignored by Jira, so comments were always returned in default order.

### Documentation

- **Migrated from Sphinx to MkDocs Material** — complete rewrite of all documentation with new content, Material theme (light/dark toggle, navigation tabs, search, code copy, content tabs).

- **Machine-readable documentation for AI agents:**

    - [`llms.txt`](https://jira2py.org/llms.txt) / [`llms-full.txt`](https://jira2py.org/llms-full.txt) — following the [llmstxt.org](https://llmstxt.org/) standard, generated by [mkdocs-llmstxt](https://github.com/pawamoy/mkdocs-llmstxt)
    - [`api-reference.json`](api-reference.json) — full API schema with signatures, types, and docstrings, generated from source code by [griffe](https://github.com/mkdocstrings/griffe)

- **Documentation dependency changes:**

    | Removed | Added |
    |---|---|
    | `sphinx` | `mkdocs-material` |
    | `pydata-sphinx-theme` | `mkdocs` |
    | `sphinx-sitemap` | `mkdocs-llmstxt` |
    | | `griffe` |

### Dependency Changes

| Removed | Added |
|---|---|
| `requests` | `httpx[http2]` |
| `pydantic` | `tenacity` |
| `pydantic-core` | |
| `email-validator` | |
| `python-dotenv` | |

## v0.3.1

Initial public release.
