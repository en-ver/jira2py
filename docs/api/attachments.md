# Attachments

Accessed via `jira.attachments`. Retrieve metadata for issue attachments.

## `get_attachment_metadata`

Get metadata for a specific attachment. Attachment IDs can be found in the `attachment` field of an issue.

```python
# Find attachment IDs from an issue
issue = jira.issues.get_issue("PROJ-123", fields="attachment")
for att in issue["fields"]["attachment"]:
    print(f"{att['id']}: {att['filename']}")

# Get detailed metadata for a specific attachment
metadata = jira.attachments.get_attachment_metadata("10001")
print(f"File: {metadata['filename']}")
print(f"Size: {metadata['size']} bytes")
print(f"Type: {metadata['mimeType']}")
print(f"URL: {metadata['content']}")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `attachment_id` | `str` | required | Attachment ID (e.g., `"10001"`) |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — attachment metadata including `id`, `filename`, `size`, `mimeType`, `content` (download URL), `author`, and `created`.

:link: [Jira REST API — Get attachment metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-id-get)
