# Issue Comments

Accessed via `jira.comments`. List, add, update, and delete comments on Jira issues.

## `get_comments`

```python
comments = jira.comments.get_comments("PROJ-123")
comments = jira.comments.get_comments("PROJ-123", order_by="-created")
```

| Parameter      | Type                        | Default  | Description                                     |
| -------------- | --------------------------- | -------- | ----------------------------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key                                 |
| `start_at`     | `int`                       | `0`      | First comment index                             |
| `max_results`  | `int`                       | `50`     | Maximum comments                                |
| `order_by`     | `str \| None`               | `None`   | `created`, `-created`, `updated`, or `-updated` |
| `expand`       | `str \| None`               | `None`   | Comma-separated expand fields                   |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters                     |

**Returns:** `dict[str, Any]`

______________________________________________________________________

## `add_comment`

The `body` must be Jira ADF.

```python
comment = jira.comments.add_comment("PROJ-123", body={
    "type": "doc",
    "version": 1,
    "content": [{
        "type": "paragraph",
        "content": [{"type": "text", "text": "This is a comment from jira2py."}],
    }],
})
```

| Parameter      | Type                        | Default  | Description                     |
| -------------- | --------------------------- | -------- | ------------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key                 |
| `body`         | `Mapping[str, Any]`         | required | Comment body in ADF format      |
| `visibility`   | `Mapping[str, Any] \| None` | `None`   | Optional visibility restriction |
| `expand`       | `str \| None`               | `None`   | Comma-separated expand fields   |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters     |
| `extra_data`   | `Mapping[str, Any] \| None` | `None`   | Additional request body data    |

**Returns:** `dict[str, Any]`

______________________________________________________________________

## `update_comment`

```python
updated = jira.comments.update_comment("PROJ-123", "10001", body={
    "type": "doc",
    "version": 1,
    "content": [{
        "type": "paragraph",
        "content": [{"type": "text", "text": "Updated comment body."}],
    }],
})
```

| Parameter      | Type                        | Default  | Description                     |
| -------------- | --------------------------- | -------- | ------------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key                 |
| `comment_id`   | `str`                       | required | Jira comment ID                 |
| `body`         | `Mapping[str, Any]`         | required | Replacement comment body in ADF |
| `visibility`   | `Mapping[str, Any] \| None` | `None`   | Optional visibility restriction |
| `expand`       | `str \| None`               | `None`   | Comma-separated expand fields   |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters     |
| `extra_data`   | `Mapping[str, Any] \| None` | `None`   | Additional request body data    |

**Returns:** `dict[str, Any]`

______________________________________________________________________

## `delete_comment`

```python
jira.comments.delete_comment("PROJ-123", "10001")
```

| Parameter      | Type                        | Default  | Description                 |
| -------------- | --------------------------- | -------- | --------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key             |
| `comment_id`   | `str`                       | required | Jira comment ID             |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters |

**Returns:** `None`

Tip

High-level helpers convert Markdown strings to ADF for you. See [High-level Helpers](https://jira2py.org/api/helpers/index.md).

[Jira REST API — Issue comments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/)
