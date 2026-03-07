# Users

Accessed via `jira.users`. Search for Jira users by name or email.

## `search_users`

Search for users matching a query string.

```python
users = jira.users.search_users("john")
for user in users:
    print(f"{user['displayName']} ({user['emailAddress']})")
    print(f"  Account ID: {user['accountId']}")
    print(f"  Active: {user['active']}")
```

```python
# Use account IDs for assigning issues
users = jira.users.search_users("jane@example.com")
if users:
    jira.issues.edit_issue("PROJ-123", fields={
        "assignee": {"accountId": users[0]["accountId"]},
    })
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | required | Search string for display name or email |
| `start_at` | `int` | `0` | Index of the first item to return (0-based) |
| `max_results` | `int` | `50` | Maximum results to return (max 1000) |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `list[dict[str, Any]]` — list of user objects with `accountId`, `displayName`, `emailAddress`, and `active`.

:link: [Jira REST API — Find users](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/#api-rest-api-3-user-search-get)
