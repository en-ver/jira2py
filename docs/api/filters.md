# Filters

Accessed via `jira.filters`. Search saved Jira filters and fetch individual filter definitions.

## `search_filters`

```python
filters = jira.filters.search_filters(max_results=10)
filters = jira.filters.search_filters(filter_name="Team", expand="owner,jql")
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `start_at` | `int` | `0` | First item index |
| `max_results` | `int` | `50` | Maximum items |
| `filter_name` | `str \| None` | `None` | Optional filter-name search |
| `filter_ids` | `list[int] \| None` | `None` | Optional saved filter IDs |
| `account_id` | `str \| None` | `None` | Optional owner account ID |
| `order_by` | `str \| None` | `None` | Optional sort field |
| `expand` | `str \| None` | `None` | Optional expand fields such as `owner,jql` |
| `override_share_permissions` | `bool \| None` | `None` | Optional Jira permission override flag |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

---

## `get_filter`

```python
saved_filter = jira.filters.get_filter("12345", expand="jql")
print(saved_filter["name"], saved_filter.get("jql"))
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `filter_id` | `str` | required | Saved filter ID |
| `expand` | `str \| None` | `None` | Optional expand fields such as `jql` |
| `override_share_permissions` | `bool \| None` | `None` | Optional Jira permission override flag |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |

**Returns:** `dict[str, Any]`

## Running a saved filter

The low-level API does not add a separate `run_filter()` endpoint wrapper. Instead:

1. fetch the saved filter with `expand="jql"`
2. read its JQL
3. run that JQL with [`jira.search.enhanced_search`](issue-search.md)

The helper-layer shortcut for this is `helpers.filters.run()`; see [High-level Helpers](helpers.md).

:link: [Jira REST API — Filters](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-filters/)
