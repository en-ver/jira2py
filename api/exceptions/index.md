# Exceptions

All exceptions are importable from the top-level package:

```python
from jira2py import (
    JiraError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)
```

For usage patterns and examples, see [Error Handling](https://jira2py.org/guide/error-handling/index.md).

## Hierarchy

```text
JiraError
├── JiraConnectionError
└── JiraAPIError
    ├── JiraAuthenticationError
    ├── JiraNotFoundError
    ├── JiraRateLimitError
    └── JiraValidationError
```

## `JiraError`

Base exception for all jira2py errors.

| Attribute  | Type               | Description                           |
| ---------- | ------------------ | ------------------------------------- |
| `message`  | `str`              | Human-readable error description      |
| `response` | `Response \| None` | The raw HTTP response, when available |

## `JiraAuthenticationError`

Raised when authentication or authorization fails (HTTP 401, 403).

Inherits from [`JiraAPIError`](#jiraapierror), so it is also caught by `except JiraAPIError` and carries the same `status_code`, `response`, and `error_messages` metadata when available. For direct construction, `status_code` defaults to `401` and `response` defaults to `None`.

## `JiraConnectionError`

Raised on network-level failures: timeouts, DNS resolution errors, connection refused.

Inherits all attributes from [`JiraError`](#jiraerror).

## `JiraAPIError`

Raised for HTTP 4xx and 5xx responses not covered by a more specific exception.

| Attribute        | Type        | Description                                          |
| ---------------- | ----------- | ---------------------------------------------------- |
| `status_code`    | `int`       | HTTP status code                                     |
| `error_messages` | `list[str]` | Error messages extracted from the Jira response body |

Includes `JiraAuthenticationError` and all other HTTP-error subclasses.

Also inherits `message` and `response` from [`JiraError`](#jiraerror). `response` may be `None` when no HTTP response object is available.

## `JiraNotFoundError`

Raised when a requested resource is not found (HTTP 404).

Inherits all attributes from [`JiraAPIError`](#jiraapierror).

## `JiraRateLimitError`

Raised when the API rate limit is exceeded (HTTP 429) and all retries have been exhausted.

| Attribute           | Type            | Description                                                               |
| ------------------- | --------------- | ------------------------------------------------------------------------- |
| `retry_after`       | `float \| None` | Seconds the server asked to wait                                          |
| `rate_limit_reason` | `str \| None`   | Which limit was hit (e.g., `jira-burst-based`, `jira-quota-tenant-based`) |
| `reset_at`          | `str \| None`   | Timestamp when the rate limit window resets                               |

Also inherits all attributes from [`JiraAPIError`](#jiraapierror).

See [Rate Limiting](https://jira2py.org/guide/rate-limiting/index.md) for how automatic retries work before this exception is raised.

## `JiraValidationError`

Raised when request validation fails (HTTP 400). Typically indicates malformed input or missing required fields.

Inherits all attributes from [`JiraAPIError`](#jiraapierror).
