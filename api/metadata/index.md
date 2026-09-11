# Metadata

Accessed via `jira.metadata`. Retrieve shared Jira Cloud metadata such as statuses and priorities.

## `get_statuses`

```python
statuses = jira.metadata.get_statuses()
for status in statuses:
    print(status["id"], status["name"])
```

| Parameter      | Type                        | Default | Description                 |
| -------------- | --------------------------- | ------- | --------------------------- |
| `extra_params` | `Mapping[str, Any] \| None` | `None`  | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

______________________________________________________________________

## `get_priorities`

```python
priorities = jira.metadata.get_priorities()
for priority in priorities:
    print(priority["id"], priority["name"])
```

| Parameter      | Type                        | Default | Description                 |
| -------------- | --------------------------- | ------- | --------------------------- |
| `extra_params` | `Mapping[str, Any] \| None` | `None`  | Additional query parameters |

**Returns:** `list[dict[str, Any]]`

[Jira REST API — Workflow statuses](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-statuses/)

[Jira REST API — Issue priorities](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-priorities/)
