# Error Handling

All errors raised by jira2py are subclasses of `JiraError`, so you can catch everything with a single `except` clause or handle specific error types individually.

## Exception Hierarchy

```
JiraError
├── JiraConnectionError            → timeouts, DNS failures, network errors
└── JiraAPIError                   → HTTP 4xx / 5xx
    ├── JiraAuthenticationError    → 401, 403
    ├── JiraNotFoundError          → 404
    ├── JiraRateLimitError         → 429
    └── JiraValidationError        → 400
```

## Catching Errors

### Catch everything

```python
from jira2py import JiraAPI, JiraError

jira = JiraAPI()

try:
    issue = jira.issues.get_issue("PROJ-123")
except JiraError as e:
    print(f"Something went wrong: {e.message}")
```

### Handle specific error types

```python
from jira2py import (
    JiraAPI,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)

jira = JiraAPI()

try:
    jira.issues.edit_issue("PROJ-123", fields={"summary": "Updated"})
except JiraNotFoundError:
    print("Issue does not exist")
except JiraValidationError as e:
    print(f"Invalid input: {e.error_messages}")
except JiraAuthenticationError:
    print("Check your credentials or permissions")
except JiraRateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
except JiraConnectionError:
    print("Network issue — check your connection")
```

## Exception Attributes

### `JiraError` (base)

All exceptions carry these attributes:

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error description |
| `response` | `Response \| None` | The raw HTTP response object, when available |

### `JiraAPIError` and subclasses

HTTP error exceptions add:

| Attribute | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code |
| `error_messages` | `list[str]` | Error messages extracted from the Jira response body |

`JiraAuthenticationError` is a subclass of `JiraAPIError`, so 401/403 failures are also caught by `except JiraAPIError` and include the same `status_code`, `response`, and `error_messages` metadata when available. When constructing one directly, `status_code` defaults to `401` and `response` defaults to `None`.

```python
from jira2py import JiraAPIError

try:
    jira.issues.create_issue(fields={"project": {"key": "INVALID"}})
except JiraAPIError as e:
    print(e.status_code)      # 400
    print(e.response)         # Response | None
    print(e.error_messages)   # ["Field 'summary' is required", ...]
```

### `JiraRateLimitError`

Rate limit exceptions include additional diagnostic attributes:

| Attribute | Type | Description |
|---|---|---|
| `retry_after` | `float \| None` | Seconds to wait, from the `Retry-After` header |
| `rate_limit_reason` | `str \| None` | Which limit was hit (e.g., `jira-burst-based`, `jira-quota-tenant-based`) |
| `reset_at` | `str \| None` | Timestamp when the rate limit window resets |

See [Rate Limiting](rate-limiting.md) for how automatic retries work before this exception is raised.

## HTTP Status Mapping

| Status Code | Exception |
|---|---|
| 400 | `JiraValidationError` |
| 401 | `JiraAuthenticationError` |
| 403 | `JiraAuthenticationError` |
| 404 | `JiraNotFoundError` |
| 429 | `JiraRateLimitError` |
| Other 4xx | `JiraAPIError` |
| 5xx | `JiraAPIError` |
| Timeout | `JiraConnectionError` |
| Network error | `JiraConnectionError` |

## Error Message Extraction

jira2py automatically parses error details from Jira's response body. It looks for messages in these fields (in order):

1. `errorMessages` — a list of error strings
2. `errors` — a dictionary of field-level errors (values are extracted)
3. `message` — a single error string

The extracted messages are available via the `error_messages` attribute on `JiraAPIError` and its subclasses.

## Exception Chaining

All exceptions preserve the original cause via Python's exception chaining. You can access the underlying error through `__cause__`:

```python
from jira2py import JiraConnectionError

try:
    jira.issues.get_issue("PROJ-123")
except JiraConnectionError as e:
    print(f"jira2py error: {e.message}")
    print(f"Original cause: {e.__cause__}")
```

For the full exception class reference, see [Exceptions](../api/exceptions.md).
