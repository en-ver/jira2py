# Issue Worklogs

Accessed via `jira.worklogs`. Retrieve the raw Jira worklog page for a single issue.

!!! note
    This is a low-level wrapper around Jira's issue worklogs endpoint. It returns the raw Jira response page and does not auto-paginate, aggregate, or build reports.

## `get_worklogs`

Get worklogs for an issue.

```python
worklogs = jira.worklogs.get_worklogs("PROJ-123")
print(f"Total worklogs: {worklogs['total']}")

for worklog in worklogs["worklogs"]:
    print(worklog["author"]["displayName"], worklog["timeSpentSeconds"])
```

```python
# Pass Jira worklog query params through extra_params
worklogs = jira.worklogs.get_worklogs(
    "PROJ-123",
    extra_params={
        "startedAfter": 1719273600000,
        "startedBefore": 1719360000000,
        "expand": "properties",
    },
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `issue_id` | `str` | required | Issue ID or key |
| `start_at` | `int` | `0` | Index of the first worklog to return (0-based) |
| `max_results` | `int` | `50` | Maximum number of worklogs to return |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters such as `startedAfter`, `startedBefore`, and `expand` |

**Returns:** `dict[str, Any]` — paginated response with `startAt`, `maxResults`, `total`, and `worklogs`.

:link: [Jira REST API — Get issue worklogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-get)
