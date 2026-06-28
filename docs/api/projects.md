# Projects

Accessed via `jira.projects`. Get, search, and list Jira projects.

## `get_project`

```python
project = jira.projects.get_project("PROJ")
project = jira.projects.get_project("10000", expand="description,lead,issueTypes")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `project_id_or_key` | `str` | required | Project key or numeric project ID |
| `expand` | `str \| None` | `None` | Comma-separated properties to expand |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `search_projects`

```python
projects = jira.projects.search_projects()
projects = jira.projects.search_projects(query="backend")
projects = jira.projects.search_projects(keys=["PROJ", "INFRA", "OPS"])
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum items per page |
| `project_ids` | `list[int] \| None` | `None` | Filter by project IDs |
| `keys` | `list[str] \| None` | `None` | Filter by project keys |
| `query` | `str \| None` | `None` | Filter by matching key or name |
| `expand` | `str \| None` | `None` | Optional expand properties |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

:link: [Jira REST API — Projects](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/)
