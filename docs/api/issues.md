# Issues

Accessed via `jira.issues`. Provides operations for creating, reading, and updating Jira issues, as well as retrieving changelogs and create/edit metadata.

## `get_issue`

Get details of a specific issue.

```python
issue = jira.issues.get_issue("PROJ-123")
print(issue["fields"]["summary"])

# Request specific fields only
issue = jira.issues.get_issue("PROJ-123", fields="summary,status,assignee")

# Expand additional properties
issue = jira.issues.get_issue("PROJ-123", expand="renderedFields,changelog")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key (e.g., `"PROJ-123"`) |
| `fields` | `str \| None` | `None` | Comma-separated field names. Use `"*all"` for all fields. |
| `expand` | `str \| None` | `None` | Comma-separated properties to expand (e.g., `"renderedFields"`) |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — issue details including `key`, `fields`, `self`, etc.

:link: [Jira REST API — Get issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get)

---

## `create_issue`

Create a new issue. Requires at minimum `project`, `issuetype`, and `summary` fields.

```python
new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "New task",
})
print(f"Created {new_issue['key']}")
```

Use [`get_create_issue_types`](#get_create_issue_types) and [`get_create_fields`](#get_create_fields) to discover which fields are available for a given project and issue type.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `fields` | `Mapping[str, Any]` | required | Issue fields |
| `update_history` | `bool` | `False` | Whether to add the project to browse history |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]` — created issue's `id`, `key`, and `self` URL.

:link: [Jira REST API — Create issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post)

---

## `edit_issue`

Update an existing issue's fields.

```python
# Simple field update
jira.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})

# Update and return the modified issue
updated = jira.issues.edit_issue(
    "PROJ-123",
    fields={"priority": {"name": "High"}},
    return_issue=True,
    expand="renderedFields",
)
print(updated["fields"]["priority"]["name"])
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `fields` | `Mapping[str, Any]` | required | Fields to update |
| `notify_users` | `bool` | `True` | Whether to send email notifications |
| `return_issue` | `bool` | `False` | Whether to return the updated issue |
| `expand` | `str \| None` | `None` | Properties to expand (only used with `return_issue=True`) |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any] | None` — the updated issue if `return_issue=True`, otherwise `None`.

:link: [Jira REST API — Edit issue](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-put)

---

## `get_changelogs`

Get the changelog history for an issue. Returns a paginated response.

```python
changelogs = jira.issues.get_changelogs("PROJ-123")
print(f"Total changes: {changelogs['total']}")

for entry in changelogs["values"]:
    print(f"{entry['created']} by {entry['author']['displayName']}")
    for item in entry["items"]:
        print(f"  {item['field']}: {item['fromString']} → {item['toString']}")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `start_at` | `int` | `0` | Index of the first item to return (0-based) |
| `max_results` | `int` | `50` | Maximum number of results |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — paginated response with `startAt`, `maxResults`, `total`, `isLast`, and `values`.

:link: [Jira REST API — Get changelogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-changelog-get)

---

## `get_edit_metadata`

Get the fields available for editing on an issue.

```python
meta = jira.issues.get_edit_metadata("PROJ-123")
for field_key, field_info in meta["fields"].items():
    print(f"{field_key}: {field_info['name']} ({field_info['schema']['type']})")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `override_screen_security` | `bool` | `False` | Include fields hidden by screen security |
| `override_editable_flag` | `bool` | `False` | Include non-editable fields |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — edit metadata including available fields and their schemas.

:link: [Jira REST API — Get edit issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-editmeta-get)

---

## `get_create_issue_types`

Get the issue types available for creating issues in a project.

```python
types = jira.issues.get_create_issue_types("PROJ")
for issue_type in types["values"]:
    print(f"{issue_type['id']}: {issue_type['name']}")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_id_or_key` | `str` | required | Project ID or key (e.g., `"PROJ"`) |
| `start_at` | `int` | `0` | Index of the first item to return |
| `max_results` | `int` | `50` | Maximum number of items |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — issue types available for the project.

:link: [Jira REST API — Get create issue metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-get)

---

## `get_create_fields`

Get the fields available when creating an issue of a specific type. Use [`get_create_issue_types`](#get_create_issue_types) first to discover the issue type ID.

```python
fields = jira.issues.get_create_fields("PROJ", "10001")
for field in fields["values"]:
    required = "required" if field.get("required") else "optional"
    print(f"{field['fieldId']}: {field['name']} ({required})")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `project_id_or_key` | `str` | required | Project ID or key |
| `issue_type_id` | `str` | required | Issue type ID (e.g., `"10001"`) |
| `start_at` | `int` | `0` | Index of the first item to return |
| `max_results` | `int` | `50` | Maximum number of items |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — fields available for creating the issue type.

:link: [Jira REST API — Get create field metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-types/#api-rest-api-3-issue-createmeta-projectidorkey-issuetypes-issuetypeid-get)
