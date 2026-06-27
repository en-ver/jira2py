# Issue Worklogs

Accessed via `jira.worklogs`. List, add, update, and delete raw Jira issue worklogs.

!!! note
    `jira.worklogs` is the low-level endpoint wrapper. For cross-issue reporting, use the helper layer's `helpers.worklogs.report()`.

## `get_worklogs`

```python
worklogs = jira.worklogs.get_worklogs("PROJ-123")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `start_at` | `int` | `0` | First worklog index |
| `max_results` | `int` | `50` | Maximum worklogs |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters such as `startedAfter`, `startedBefore`, and `expand` |

**Returns:** `dict[str, Any]`

---

## `add_worklog`

```python
worklog = jira.worklogs.add_worklog("PROJ-123", "1h 30m")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `time_spent` | `str` | required | Jira time-tracking duration |
| `started` | `str \| None` | `None` | Optional started timestamp |
| `comment` | `Mapping[str, Any] \| None` | `None` | Optional ADF comment |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]`

---

## `update_worklog`

```python
updated = jira.worklogs.update_worklog("PROJ-123", "10010", time_spent="2h")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `worklog_id` | `str` | required | Jira worklog ID |
| `time_spent` | `str \| None` | `None` | Optional replacement duration |
| `started` | `str \| None` | `None` | Optional replacement started timestamp |
| `comment` | `Mapping[str, Any] \| None` | `None` | Optional replacement ADF comment |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]`

---

## `delete_worklog`

```python
jira.worklogs.delete_worklog("PROJ-123", "10010")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `issue_id` | `str` | required | Issue ID or key |
| `worklog_id` | `str` | required | Jira worklog ID |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `None`

:link: [Jira REST API — Issue worklogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/)
