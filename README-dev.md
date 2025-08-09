# jira2py

## Upgrade dependencies

List the installed packages:

```bash
uv pip list | grep -f requirements.txt
```

> [!NOTE]
> Dependencies are now specified with compatible version ranges (e.g., `>=X.Y.Z,<X.Y+1.0`) instead of exact pins to allow for easier security updates while maintaining stability.

## Rate Limiting Configuration

The jira2py library now includes built-in support for handling JIRA API rate limits. The following parameters can be configured when initializing any of the client classes:

- `max_retries` (int, default=3): Maximum number of retries for rate-limited requests
- `initial_retry_delay` (float, default=1.0): Initial delay in seconds for retry backoff
- `max_retry_delay` (float, default=60.0): Maximum delay in seconds for retry backoff

Example usage:
```python
from jira2py import Issues

# Configure custom rate limiting parameters
issues = Issues(
    max_retries=5,
    initial_retry_delay=2.0,
    max_retry_delay=120.0
)
```

The implementation includes:
- Automatic detection of HTTP 429 responses
- Respect for `Retry-After` and `Beta-Retry-After` headers
- Exponential backoff with jitter to prevent thundering herd
- Proper error handling when max retries are exceeded
