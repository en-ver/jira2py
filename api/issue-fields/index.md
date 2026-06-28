# Issue Fields

Accessed via `jira.fields`. List system and custom fields configured in your Jira instance.

## `get_fields`

Get all system and custom issue fields.

```python
fields = jira.fields.get_fields()

for field in fields:
    kind = "custom" if field["custom"] else "system"
    print(f"{field['id']}: {field['name']} ({kind})")
```

```python
# Find a specific custom field by name
target = "Story Points"
match = next((f for f in jira.fields.get_fields() if f["name"] == target), None)
if match:
    print(f"Use field ID '{match['id']}' for {target}")
```

This method takes no parameters.

**Returns:** `list[dict[str, Any]]` — list of field objects with `id`, `name`, `custom`, `schema`, and other properties.

[Jira REST API — Get fields](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get)
