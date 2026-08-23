# Issues

Accessed via `jira.issues`. Create, read, edit, and transition Jira Cloud issues, plus related metadata.

## `get_issue`

```python
issue = jira.issues.get_issue("PROJ-123", fields=["summary", "status", "assignee"])
issue = jira.issues.get_issue("PROJ-123", fields=["*navigable", "-description"])
issue = jira.issues.get_issue("PROJ-123", expand="renderedFields,changelog")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `fields` | `Sequence[str] \| None` | `None` | Exact Jira field selectors, one selector per item |
| `expand` | `str \| None` | `None` | Comma-separated properties to expand |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional raw query parameters that take priority over named parameters |

A supplied `fields` sequence must be non-empty. Each item must be a non-blank, unpadded string with no comma; scalar strings and bytes are rejected. jira2py serializes the sequence for this endpoint immediately before the request, preserving selector order and duplicates without adding fields or an `expand` value.

`fields=None` omits the query parameter so Jira chooses its default. As with every low-level API method, `extra_params` has precedence: `extra_params["fields"]` is a raw override and is not interpreted or validated as the named sequence.

!!! warning "Selectors can be broad"
    `"*all"`, `"*navigable"`, and negative selectors such as `"-description"` are forwarded exactly as supplied. They can still produce broad responses, including when a negative selector is used alone. Choose selectors deliberately and let Jira validate which ones it supports.

**Returns:** `dict[str, Any]`

---

## `create_issue`

```python
new_issue = jira.issues.create_issue(fields={
    "project": {"key": "PROJ"},
    "issuetype": {"name": "Task"},
    "summary": "New task",
})
```

Use [`get_create_issue_types`](#get_create_issue_types) and [`get_create_fields`](#get_create_fields) to discover valid create metadata.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `fields` | `Mapping[str, Any]` | required | Issue fields |
| `update_history` | `bool` | `False` | Whether to add the project to browse history |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]`

---

## `edit_issue`

```python
jira.issues.edit_issue("PROJ-123", fields={"summary": "Updated summary"})
updated = jira.issues.edit_issue(
    "PROJ-123",
    fields={"priority": {"name": "High"}},
    return_issue=True,
)
```

Use this generic field-edit pathway if you need to set assignee fields supported by your Jira screens. jira2py does **not** add a dedicated assign API.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `fields` | `Mapping[str, Any]` | required | Fields to update |
| `notify_users` | `bool` | `True` | Whether to send email notifications |
| `return_issue` | `bool` | `False` | Whether to return the updated issue |
| `expand` | `str \| None` | `None` | Properties to expand |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any] \| None`

---

## `get_transitions`

```python
transitions = jira.issues.get_transitions("PROJ-123")
transitions = jira.issues.get_transitions("PROJ-123", expand="transitions.fields")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `expand` | `str \| None` | `None` | Optional expand value such as `transitions.fields` |
| `transition_id` | `str \| None` | `None` | Optional transition ID filter |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` with a `transitions` list.

---

## `transition_issue`

```python
jira.issues.transition_issue("PROJ-123", transition_id="31")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `transition_id` | `str` | required | Explicit Jira transition ID |
| `fields` | `Mapping[str, Any] \| None` | `None` | Optional fields to set while transitioning |
| `update` | `Mapping[str, Any] \| None` | `None` | Optional Jira update operations |
| `history_metadata` | `Mapping[str, Any] \| None` | `None` | Optional transition history metadata |
| `properties` | `Sequence[Mapping[str, Any]] \| None` | `None` | Optional issue properties |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any] \| None`

---

## `get_changelogs`

```python
changelogs = jira.issues.get_changelogs("PROJ-123")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum results |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `get_edit_metadata`

```python
meta = jira.issues.get_edit_metadata("PROJ-123")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `override_screen_security` | `bool` | `False` | Override screen security |
| `override_editable_flag` | `bool` | `False` | Override editable flag |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `get_create_issue_types`

```python
types = jira.issues.get_create_issue_types("PROJ")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `project_id_or_key` | `str` | required | Project ID or key |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum items |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `get_create_fields`

```python
fields = jira.issues.get_create_fields("PROJ", "10001")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `project_id_or_key` | `str` | required | Project ID or key |
| `issue_type_id` | `str` | required | Issue type ID |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum items |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

:link: [Jira REST API — Issues group](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)
