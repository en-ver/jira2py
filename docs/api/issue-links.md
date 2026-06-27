# Issue Links

Accessed via `jira.issue_links`. List issue links, list link types, create links, and delete links.

## `get_issue_links`

```python
links = jira.issue_links.get_issue_links("PROJ-123")
for link in links:
    print(link["id"], link["type"]["name"])
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

---

## `get_link_types`

```python
result = jira.issue_links.get_link_types()
```

This method takes no parameters.

**Returns:** `dict[str, Any]`

---

## `create_link`

```python
jira.issue_links.create_link("Blocks", "PROJ-1", "PROJ-2")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `link_type_name` | `str` | required | Link type name |
| `inward_issue_key` | `str` | required | Key of the inward issue |
| `outward_issue_key` | `str` | required | Key of the outward issue |

**Returns:** `None`

---

## `delete_link`

```python
jira.issue_links.delete_link("10001")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `link_id` | `str` | required | Issue-link ID |

**Returns:** `None`

:link: [Jira REST API — Issue links](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/)
