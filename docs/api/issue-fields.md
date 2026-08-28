# Issue Fields

Accessed via `jira.fields`. It provides the legacy all-fields response and a one-page searchable field catalog.

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
# get_fields() remains an all-fields, unpaginated response.
target = "Story Points"
match = next((f for f in jira.fields.get_fields() if f["name"] == target), None)
if match:
    print(f"Use field ID '{match['id']}' for {target}")
```

This method takes no parameters.

**Returns:** `list[dict[str, Any]]` — list of field objects with `id`, `name`, `custom`, `schema`, and other properties.

:link: [Jira REST API — Get fields](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get)

---

## `search_fields`

Get one raw page from Jira's stable field-search endpoint. Use canonical field `id` values (for example, `summary` or `customfield_10001`), not display names, when filtering or using a field to update an issue.

```python
page = jira.fields.search_fields(
    query="points",
    field_ids=["customfield_10001"],
    field_types=["custom"],
    project_ids=[10000],
    order_by="name",
    expand="key,stableId",
)

for field in page["values"]:
    print(field["id"], field["name"])

if not page["isLast"]:
    next_page = jira.fields.search_fields(
        start_at=page["startAt"] + len(page["values"]),
        query="points",
        field_ids=["customfield_10001"],
        field_types=["custom"],
        project_ids=[10000],
    )
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `start_at` | `int` | `0` | First field index in the Jira page |
| `max_results` | `int` | `50` | Maximum fields in the Jira page |
| `query` | `str \| None` | `None` | Case-insensitive partial match against field name or description |
| `field_ids` | `list[str] \| None` | `None` | Canonical Jira field IDs (`id` query parameter) |
| `field_types` | `list[str] \| None` | `None` | Jira field types: `"system"` and/or `"custom"` |
| `project_ids` | `list[int] \| None` | `None` | Numeric Jira project IDs for project context filtering |
| `order_by` | `str \| None` | `None` | Jira ordering expression, such as `"name"` or `"-lastUsed"` |
| `expand` | `str \| None` | `None` | Comma-separated Jira field expansions, such as `"key,stableId"` |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Raw query parameters; matching keys override named parameters |

**Returns:** `dict[str, Any]` — exactly one Jira page, including raw `values` and Jira pagination metadata such as `startAt`, `maxResults`, `total`, and `isLast` when supplied by Jira.

!!! warning "Project context is not screen applicability"
    Jira documents `/field/search` for **Classic Jira projects**. `project_ids` is Jira's project-context/access filter only: it does not accept an issue type and does not establish whether a field is present on a create or edit screen. Use `helpers.metadata.create_fields()` for create-screen metadata and `helpers.metadata.edit_fields()` for an existing issue's edit metadata.

:link: [Jira REST API — Get fields paginated](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-search-get)
