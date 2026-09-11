# Attachments

Accessed via `jira.attachments`. List issue attachments, read metadata, download content, upload files, and delete attachments.

## `get_issue_attachments`

```python
attachments = jira.attachments.get_issue_attachments("PROJ-123")
for attachment in attachments:
    print(attachment["id"], attachment["filename"])
```

| Parameter      | Type                        | Default  | Description                 |
| -------------- | --------------------------- | -------- | --------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key             |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

______________________________________________________________________

## `get_attachment_metadata`

```python
metadata = jira.attachments.get_attachment_metadata("10001")
```

| Parameter       | Type                        | Default  | Description                 |
| --------------- | --------------------------- | -------- | --------------------------- |
| `attachment_id` | `str`                       | required | Attachment ID               |
| `extra_params`  | `Mapping[str, Any] \| None` | `None`   | Additional query parameters |

**Returns:** `dict[str, Any]`

______________________________________________________________________

## `download_attachment_content`

```python
with open("download.bin", "wb") as destination:
    observed = jira.attachments.download_attachment_content(
        "10001", destination, max_bytes=100 * 1024 * 1024
    )
```

| Parameter       | Type                        | Default  | Description                                            |
| --------------- | --------------------------- | -------- | ------------------------------------------------------ |
| `attachment_id` | `str`                       | required | Attachment ID                                          |
| `destination`   | `BinaryIO`                  | required | Caller-owned binary destination                        |
| `max_bytes`     | `int`                       | required | Positive cumulative byte limit                         |
| `expected_size` | `int \| None`               | `None`   | Optional exact byte count; zero requires empty content |
| `redirect`      | `bool \| None`              | `None`   | Optional explicit redirect parameter                   |
| `extra_params`  | `Mapping[str, Any] \| None` | `None`   | Additional query parameters                            |

**Returns:** `int` observed bytes written.

The transfer starts at the configured Jira endpoint, follows Jira redirects, and enforces cumulative and optional expected-size limits while streaming. It does not close, flush, rewind, truncate, or clean up `destination`; callers own any partial output after a failure. High-level managed Markdown image writes retain their separate private, authenticated no-follow bounded reader for dimension acquisition.

______________________________________________________________________

## `add_attachment`

```python
created = jira.attachments.add_attachment(
    "PROJ-123",
    filename="error.log",
    content=b"example",
    content_type="text/plain",
)
```

| Parameter      | Type                        | Default  | Description                 |
| -------------- | --------------------------- | -------- | --------------------------- |
| `issue_id`     | `str`                       | required | Issue ID or key             |
| `filename`     | `str`                       | required | Filename to send to Jira    |
| `content`      | `bytes`                     | required | Raw file bytes              |
| `content_type` | `str \| None`               | `None`   | Optional MIME type          |
| `extra_params` | `Mapping[str, Any] \| None` | `None`   | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

______________________________________________________________________

## `delete_attachment`

```python
jira.attachments.delete_attachment("10001")
```

| Parameter       | Type                        | Default  | Description                 |
| --------------- | --------------------------- | -------- | --------------------------- |
| `attachment_id` | `str`                       | required | Attachment ID               |
| `extra_params`  | `Mapping[str, Any] \| None` | `None`   | Additional query parameters |

**Returns:** `None`

Tip

For atomic local file downloads, see the helper-layer attachment methods in [High-level Helpers](https://jira2py.org/api/helpers/index.md).

[Jira REST API — Attachments](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/)
