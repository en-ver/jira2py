# Configuration

## Credentials

`JiraAPI` authenticates to **Jira Cloud** with three values:

| Parameter   | Environment Variable | Description                      |
| ----------- | -------------------- | -------------------------------- |
| `url`       | `JIRA_URL`           | Base URL of your Jira Cloud site |
| `username`  | `JIRA_USER`          | Atlassian account email          |
| `api_token` | `JIRA_API_TOKEN`     | Jira API token                   |

You can supply them in two supported ways:

1. **Environment variables** — the default when you call `JiraAPI()` with no explicit credentials file.
1. **An explicit JSON credentials file path** via `credentials_file=...`.

```json
{
  "url": "https://your-domain.atlassian.net",
  "username": "your-email@example.com",
  "api_token": "your-api-token"
}
```

### Resolution order

jira2py resolves credentials in this order:

1. Explicit `url`, `username`, and `api_token` arguments
1. Values loaded from `credentials_file`, if you passed one
1. Environment variables (`JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`)

There is **no default credentials file path**. If you do not pass `credentials_file`, jira2py uses environment variables.

```python
from jira2py import JiraAPI

jira = JiraAPI()  # environment variables
jira = JiraAPI(credentials_file="./jira-credentials.json")
jira = JiraAPI(credentials_file="./jira-credentials.json", api_token="override-token")
```

### Validation

Credentials are validated at construction time:

- all three values must be non-empty after stripping whitespace
- the URL must start with `http://` or `https://`
- a trailing `/` on the URL is removed automatically
- if `credentials_file` is passed, it must be valid JSON containing `url`, `username`, and `api_token`

```python
from jira2py import JiraAPI

JiraAPI(url="", username="user@example.com", api_token="token")
JiraAPI(url="not-a-url", username="user@example.com", api_token="token")
JiraAPI(credentials_file="./missing.json")
```

### Immutability

Credentials are immutable. To use different credentials, create a new `JiraAPI` instance.

## Retry Settings

jira2py automatically retries HTTP 429 responses.

| Parameter         | Default | Description                                          |
| ----------------- | ------- | ---------------------------------------------------- |
| `max_retries`     | `4`     | Maximum retry attempts on 429 responses              |
| `max_retry_delay` | `30.0`  | Upper bound on wait time between retries, in seconds |

```python
jira = JiraAPI(max_retries=2, max_retry_delay=10.0)
```

See [Rate Limiting](https://jira2py.org/guide/rate-limiting/index.md) for details.

## HTTP Client

The HTTP client defaults are:

| Setting         | Value      |
| --------------- | ---------- |
| HTTP/2          | Enabled    |
| Request timeout | 30 seconds |
| Connect timeout | 10 seconds |

Connections are reused across requests for better performance.
