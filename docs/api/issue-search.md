# Issue Search

Accessed via `jira.search`. Search for issues using JQL (Jira Query Language).

## `enhanced_search`

Search for issues using a JQL query. Returns paginated results.

```python
# One page
results = jira.search.enhanced_search("project = PROJ ORDER BY created DESC")
print(f"Returned {len(results['issues'])} issues")

for issue in results["issues"]:
    print(f"{issue['key']}: {issue['fields']['summary']}")
```

```python
# Request specific fields
results = jira.search.enhanced_search(
    "project = PROJ AND status = 'In Progress'",
    fields=["summary", "status", "assignee"],
    max_results=25,
)
```

```python
# Accumulate pages. Keep the JQL and fields unchanged, and treat each token as opaque.
jql = "project = PROJ ORDER BY created DESC"
fields = ["summary", "status", "assignee"]
issues = []
next_page_token = None

while True:
    page = jira.search.enhanced_search(
        jql,
        next_page_token=next_page_token,
        max_results=100,
        fields=fields,
    )
    issues.extend(page["issues"])
    next_page_token = page.get("nextPageToken")
    if not next_page_token:
        break
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `jql` | `str` | required | JQL query string |
| `next_page_token` | `str \| None` | `None` | Token for fetching the next page of results. Omitted from the request body when `None`. |
| `max_results` | `int` | `50` | Maximum items per page |
| `fields` | `list[str] \| None` | `None` | Fields to return (e.g., `["summary", "status"]`). Use `["*all"]` for all. Omitted from the request body when `None`. |
| `expand` | `str \| None` | `None` | Comma-separated properties to expand. Omitted from the request body when `None`. |
| `extra_params` | `Mapping[str, Any] \| None` | `None` | Additional query parameters |
| `extra_data` | `Mapping[str, Any] \| None` | `None` | Additional request body data |

**Returns:** `dict[str, Any]` — one raw search-response page. It includes `issues` and may include `total` and `nextPageToken`. To continue, pass `nextPageToken` unchanged with the same JQL and fields. Stop when no token is returned rather than relying on `total`.

:link: [Jira REST API — Search for issues using JQL enhanced search](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post)
