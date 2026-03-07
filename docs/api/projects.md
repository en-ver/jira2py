# Projects

Accessed via `jira.projects`. Search and list Jira projects.

## `search_projects`

Search for projects with optional filtering and pagination.

```python
# List all projects
projects = jira.projects.search_projects()
for project in projects["values"]:
    print(f"{project['key']}: {project['name']}")
```

```python
# Search by name or key
projects = jira.projects.search_projects(query="backend")
```

```python
# Filter by specific keys
projects = jira.projects.search_projects(keys=["PROJ", "INFRA", "OPS"])
```

```python
# Include additional details
projects = jira.projects.search_projects(
    expand="description,lead,issueTypes",
)
for project in projects["values"]:
    print(f"{project['key']}: {project.get('description', '')}")
    print(f"  Lead: {project['lead']['displayName']}")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start_at` | `int` | `0` | Index of the first item to return (0-based) |
| `max_results` | `int` | `50` | Maximum items per page (max 100) |
| `project_ids` | `list[int] \| None` | `None` | Filter by project IDs (up to 50) |
| `keys` | `list[str] \| None` | `None` | Filter by project keys (up to 50) |
| `query` | `str \| None` | `None` | Filter by matching key or name (case insensitive) |
| `expand` | `str \| None` | `None` | Comma-separated properties to expand: `description`, `projectKeys`, `lead`, `issueTypes`, `url`, `insight` |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]` — paginated results with `startAt`, `maxResults`, `total`, `isLast`, and `values`.

:link: [Jira REST API — Search projects](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get)
