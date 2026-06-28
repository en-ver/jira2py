# Users

Accessed via `jira.users`. Search Jira users or inspect the current authenticated Jira user.

## `search_users`

```python
users = jira.users.search_users("john")
for user in users:
    print(user["displayName"], user["accountId"])
```

If you need to set assignee fields, use the returned account IDs with the generic issue edit pathway:

```python
users = jira.users.search_users("jane@example.com")
if users:
    jira.issues.edit_issue("PROJ-123", fields={
        "assignee": {"accountId": users[0]["accountId"]},
    })
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `query` | `str` | required | Search string for display name or email |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum results |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

---

## `get_current_user`

```python
me = jira.users.get_current_user()
print(me["displayName"], me["accountId"])
```

This is the low-level current-user endpoint used by helper auth/status flows.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

:link: [Jira REST API — Find users](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/#api-rest-api-3-user-search-get)

:link: [Jira REST API — Get current user](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-myself/#api-rest-api-3-myself-get)
