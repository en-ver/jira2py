# Issue Comments

Accessed via `jira.comments`. List and add comments on issues.

## `get_comments`

Get comments for an issue. Returns paginated results.

```python
comments = jira.comments.get_comments("PROJ-123")
print(f"Total comments: {comments['total']}")

for comment in comments["comments"]:
    print(f"{comment['author']['displayName']}: {comment['body']}")
```

```python
# Most recent comments first
comments = jira.comments.get_comments("PROJ-123", order_by="-created")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `start_at` | `int` | `0` | Index of the first comment to return (0-based) |
| `max_results` | `int` | `100` | Maximum number of comments |
| `order_by` | `str \| None` | `None` | Sort order: `"created"`, `"-created"`, `"updated"`, or `"-updated"` |
| `expand` | `str \| None` | `None` | Comma-separated fields to expand (e.g., `"renderedBody"`) |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — paginated response with `startAt`, `maxResults`, `total`, and `comments`.

:link: [Jira REST API — Get comments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-get)

---

## `add_comment`

Add a comment to an issue. The comment body must be in [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/).

```python
comment = jira.comments.add_comment("PROJ-123", body={
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "This is a comment from jira2py."}
            ],
        }
    ],
})
print(f"Comment added: {comment['id']}")
```

```python
# Restrict visibility to a role
comment = jira.comments.add_comment(
    "PROJ-123",
    body={
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Internal note."}
                ],
            }
        ],
    },
    visibility={"type": "role", "value": "Administrators"},
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `body` | `Mapping[str, Any]` | required | Comment body in ADF format |
| `visibility` | `Mapping[str, Any] \| None` | `None` | Visibility restriction (e.g., `{"type": "role", "value": "Administrators"}`) |
| `expand` | `str \| None` | `None` | Comma-separated fields to expand |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]` — created comment details including `id`, `body`, `author`, and `created`.

!!! tip
    Building ADF by hand can be verbose. Libraries like [marklassian](https://pypi.org/project/marklassian/) can convert Markdown to ADF for you.

:link: [Jira REST API — Add comment](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/#api-rest-api-3-issue-issueidorkey-comment-post)
