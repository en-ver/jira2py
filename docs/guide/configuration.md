# Configuration

## Credentials

`JiraAPI` requires three credentials to authenticate with your Jira Cloud instance:

| Parameter   | Environment Variable | Description                                                                                                   |
| ----------- | -------------------- | ------------------------------------------------------------------------------------------------------------- |
| `url`       | `JIRA_URL`           | Base URL of your Jira instance                                                                                |
| `username`  | `JIRA_USER`          | Email address of your Atlassian account                                                                       |
| `api_token` | `JIRA_API_TOKEN`     | API token from your [Atlassian account settings](https://id.atlassian.com/manage-profile/security/api-tokens) |

### Resolution Order

Each credential is resolved independently using the same logic:

1. If an explicit argument is provided, it is used
2. Otherwise, the corresponding environment variable is checked
3. If neither is set, a `ValueError` is raised

This means you can mix both methods — for example, keep the URL and username in the environment and pass only the token at runtime:

```python
from jira2py import JiraAPI

# JIRA_URL and JIRA_USER are set in the environment
jira = JiraAPI(api_token="your-api-token")
```

### Validation

Credentials are validated at construction time:

- All three values must be non-empty after stripping whitespace
- The URL must start with `http://` or `https://`
- A trailing `/` on the URL is removed automatically

```python
from jira2py import JiraAPI

# These all raise ValueError immediately
JiraAPI(url="", username="user@example.com", api_token="token")       # empty URL
JiraAPI(url="not-a-url", username="user@example.com", api_token="token")  # missing scheme
JiraAPI()  # no env vars set, no arguments provided
```

### Immutability

Credentials are immutable. Once a `JiraAPI` instance is created, its credentials cannot be changed. To use different credentials, create a new instance.

## Retry Settings

jira2py automatically retries requests that receive an HTTP 429 (rate limit) response. You can configure this behavior through two parameters on `JiraAPI`:

| Parameter | Default | Description |
|---|---|---|
| `max_retries` | `4` | Maximum number of retry attempts on 429 responses. Set to `0` to disable. |
| `max_retry_delay` | `30.0` | Upper bound on the wait time between retries, in seconds. |

```python
jira = JiraAPI(max_retries=2, max_retry_delay=10.0)
```

See [Rate Limiting](rate-limiting.md) for the retry strategy, backoff behavior, and `Retry-After` header handling.

## HTTP Client

The HTTP client is preconfigured with sensible defaults:

| Setting | Value |
|---|---|
| HTTP/2 | Enabled |
| Request timeout | 30 seconds |
| Connect timeout | 10 seconds |

Connections are reused across requests for better performance. Resources are cleaned up automatically when the Python process exits.
