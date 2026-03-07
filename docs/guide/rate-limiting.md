# Rate Limiting

Jira Cloud enforces [rate limits](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/) to protect the platform from excessive API usage. When a rate limit is hit, Jira responds with HTTP 429 (Too Many Requests).

jira2py handles this automatically — no configuration required. Requests that receive a 429 response are retried transparently, and your code only sees an error if all retries are exhausted.

## How It Works

When a request receives a 429 response:

1. The client checks the `Retry-After` header for a server-specified wait time
2. It calculates the delay using the appropriate backoff strategy (see below)
3. A warning is logged with the attempt number, `RateLimit-Reason`, and `Retry-After` values
4. The request is retried after the delay
5. If all retries are exhausted, a `JiraRateLimitError` is raised

Only HTTP 429 responses are retried. All other errors — including 500, 401, 404, etc. — propagate immediately.

## Backoff Strategy

The delay between retries depends on whether Jira includes a `Retry-After` header in the 429 response.

### With `Retry-After` header

The server-specified wait time is used as the minimum delay. Additive jitter of 0–30% is applied above that minimum to avoid thundering herd problems when multiple clients are rate-limited simultaneously:

```
delay = retry_after + random(0, retry_after × 0.3)
```

### Without `Retry-After` header

Exponential backoff is used with a base delay of 5 seconds. Multiplicative jitter (0.7×–1.3×) is applied to spread out retries:

```
delay = 5 × 2^(attempt - 1) × random(0.7, 1.3)
```

This produces approximate delays of 5s, 10s, 20s, 40s for attempts 1 through 4.

### Delay cap

Regardless of the strategy, the computed delay is capped at `max_retry_delay` (default: 30 seconds).

## Configuration

Retry behavior is configured through `JiraAPI` constructor parameters. See [Configuration](configuration.md) for the parameter reference.

```python
from jira2py import JiraAPI

# Custom: fewer retries, shorter max wait
jira = JiraAPI(max_retries=2, max_retry_delay=10.0)

# Disable retries entirely
jira = JiraAPI(max_retries=0)
```

## Logging

Retry attempts are logged at `WARNING` level via the `jira2py` logger. Each log message includes:

- Attempt number
- `RateLimit-Reason` header value (e.g., `jira-burst-based`, `jira-quota-tenant-based`)
- `Retry-After` header value

To see retry logs:

```python
import logging

logging.basicConfig(level=logging.WARNING)
```

## When Retries Are Exhausted

If all retry attempts fail, a `JiraRateLimitError` is raised. See [Error Handling](error-handling.md) for how to catch it and inspect its diagnostic attributes (`retry_after`, `rate_limit_reason`, `reset_at`).
