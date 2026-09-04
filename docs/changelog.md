# Changelog

## Unreleased

### Breaking changes

- `Issues.get_issue()` now accepts `Sequence[str] | None` for `fields`. A supplied sequence is validated and serialized only at the Get Issue endpoint; comma-delimited scalar strings are no longer accepted.
- Removed `IssueHelpers.read()` and its fixed retrieval profile. Retrieve issues directly with `JiraAPI`, which now remains the sole full-issue retrieval authority.
- `fields=None` omits the parameter for Jira's default behavior unless raw `extra_params["fields"]` overrides it. Selectors are forwarded exactly, without implicit fields or `expand`; wildcard and negative selectors may be broad.
- High-level Markdown inputs shaped as `[~accountId:<id>]` now create Jira mentions rather than literal text.

```python
# Before (removed)
from jira2py.helpers import JiraHelpers

helpers = JiraHelpers(api)
api.issues.get_issue("PROJ-123", fields="summary,status")
helpers.issues.read("PROJ-123", extra_fields=["customfield_10001"])

# After
from jira2py.helpers import format_issue

issue = api.issues.get_issue(
    "PROJ-123",
    fields=["summary", "status", "customfield_10001"],
)
text = format_issue(
    issue,
    browse_url=f"{api.credentials.url}/browse/{issue['key']}",
)
```

### Added

- Added universal Jira account mentions to high-level Markdown writes: issue create/edit descriptions, `environment`, compatible custom textarea fields, comment add/update bodies, and worklog add/update comments. Input accepts case-insensitive `accountId`, including IDs containing `:`. Formatted ADF reads remain presentation-only through pyadf and can lose mention identity if edited and written back; raw ADF is required for identity-safe edits until dedicated formatted read/edit/write support is added.

- Added named low-level transition-discovery controls for `includeUnavailableTransitions`, `skipRemoteOnlyCondition`, and `sortByOpsBarAndStatus`, while retaining the existing positional arguments and `extra_params` precedence.
- Added focused transition discovery through `MetadataHelpers.transitions(..., transition_id=..., include_unavailable_transitions=...)`. It always expands `transitions.fields`, keeps Jira's complete raw transition envelope in helper data, and presents destination IDs/names, availability and workflow indicators, plus screen field keys/names/requirements/operations.
- Added Jira-native `fields` and `update` mappings to `IssueHelpers.transition()`. The helper rejects exact overlap between their field keys, forwards neither submitted body in its result, and leaves Jira as the validator for screen requirements and field values. Successful helper transition results now add `verified: false`: Jira accepted the request, but jira2py did not perform a verification read and reports the destination only as expected.

- Added one-page `IssueFields.search_fields()` support for Jira's stable `/field/search` endpoint, including canonical field IDs, system/custom type filters, project IDs, ordering, expansions, and raw query overrides. `IssueFields.get_fields()` is unchanged.
- Added `MetadataHelpers.list_fields()` for one searchable raw field page with concise canonical-ID text and optional project-key-to-numeric-ID context resolution. Jira documents field search for Classic projects; project context does not determine issue-type or create/edit-screen applicability.
- Added exact case-sensitive raw `fieldId` filtering to ordinary and known-ID changelog helpers. Ordinary changelog retrieval also supports optional post-filter event pagination with `result_page` metadata after all Jira pages, timestamp filtering, item pruning, and empty-event removal.
- Added `Issues.get_changelogs_by_ids()` for Jira's official issue-scoped changelog-list POST endpoint.
- Added `JiraHelpers.changelogs` for complete changelog retrieval with optional UTC-normalized half-open creation bounds, plus one-request known-ID retrieval.
- Added permissive changelog/page models and concise changelog helper text while retaining complete original Jira mappings in structured helper output.

- Added public pure `jira2py.helpers.format_issue(data, *, browse_url=None)` for optional presence-aware issue text presentation without I/O, mutation, or retrieval policy.

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
