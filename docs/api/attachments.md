# Attachments

Accessed via `jira.attachments`. List issue attachments, read metadata, download content, upload files, and delete attachments.

## `get_issue_attachments`

```python
attachments = jira.attachments.get_issue_attachments("PROJ-123")
for attachment in attachments:
    print(attachment["id"], attachment["filename"])
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

---

## `get_attachment_metadata`

```python
metadata = jira.attachments.get_attachment_metadata("10001")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `attachment_id` | `str` | required | Attachment ID |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `download_attachment_content`

```python
content = jira.attachments.download_attachment_content("10001")
with open("download.bin", "wb") as fh:
    fh.write(content)
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `attachment_id` | `str` | required | Attachment ID |
| `redirect` | `bool \| None` | `None` | Optional explicit redirect parameter |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `bytes`

---

## `add_attachment`

```python
created = jira.attachments.add_attachment(
    "PROJ-123",
    filename="error.log",
    content=b"example",
    content_type="text/plain",
)
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `filename` | `str` | required | Filename to send to Jira |
| `content` | `bytes` | required | Raw file bytes |
| `content_type` | `str \| None` | `None` | Optional MIME type |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

---

## `delete_attachment`

```python
jira.attachments.delete_attachment("10001")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `attachment_id` | `str` | required | Attachment ID |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `None`

!!! tip
    For download planning and local file writes, see the helper-layer attachment methods in [High-level Helpers](helpers.md).

:link: [Jira REST API — Attachments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/)
