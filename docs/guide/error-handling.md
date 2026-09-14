# Error Handling

`JiraError` is the root of jira2py's custom low-level HTTP, transport, and attachment-protocol error hierarchy. It is not a catch-all for every exception a jira2py call can raise.

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

### Catch custom low-level errors

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

## Helper, built-in, and non-raising outcomes

High-level helpers use an independent hierarchy, imported from `jira2py.helpers`:

```text
JiraHelperError
├── JiraHelperValidationError
├── JiraHelperConfigError
├── JiraHelperOperationError
└── AttachmentError
    └── AttachmentDownloadError
```

`JiraHelperError` does not inherit from `JiraError`. Local credential, input, and response checks can raise built-in `ValueError` or `TypeError`, and helper model parsing can raise model-validation errors. Catch the hierarchy or built-in error appropriate to the operation rather than assuming `JiraError` covers every failure.

Create-metadata discovery is scoped more narrowly: `helpers.metadata.issue_types()` and `create_fields()` raise `JiraHelperValidationError` for invalid arguments and for an unknown type after terminal discovery. Jira request failures, malformed create-metadata pages or collections, non-advancing pagination, and create-metadata model-validation failures raise `JiraHelperOperationError`; request and model-validation failures preserve their underlying cause. They never return a partial aggregate.

`helpers.auth.status()` converts a failure from the current-user endpoint into `HelperResult.data` with `ok=False`; inspect that flag. This conversion does not guarantee that unrelated post-response processing cannot raise.

## Exception Attributes

### `JiraError` (base)

These custom low-level exceptions carry these attributes:

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable error description |
| `response` | `Response \| None` | The raw HTTP response object, when available; sanitized attachment and managed-media paths expose no response object |

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

Many wrapped errors preserve their original cause through Python exception chaining, but the presence of `__cause__` or `__context__` is path-dependent and must not be relied on. Directly raised errors may have neither. Security-sensitive attachment and managed-media paths suppress or avoid exposing sensitive underlying details and response objects.

```python
from jira2py import JiraConnectionError

try:
    jira.issues.get_issue("PROJ-123")
except JiraConnectionError as e:
    print(f"jira2py error: {e.message}")
    if e.__cause__ is not None:
        print(f"Original cause: {e.__cause__}")
```

For the full exception class reference, see [Exceptions](../api/exceptions.md).
