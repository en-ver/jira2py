# High-level Helpers

`jira2py.helpers.JiraHelpers` is an optional high-level facade for common **Jira Cloud** workflows.

Use it when you want grouped operations plus readable `HelperResult` output instead of raw Jira REST payloads. Full issue reads stay structured-first on `JiraAPI`; public `format_issue` can render an already-retrieved response when needed.

## Import path

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers, format_issue

api = JiraAPI()
helpers = JiraHelpers(api)
```

## Helper groups

```python
helpers.auth
helpers.issues
helpers.search
helpers.comments
helpers.changelogs
helpers.worklogs
helpers.attachments
helpers.metadata
helpers.links
helpers.filters
```

| Group | Use for |
| --- | --- |
| `helpers.auth` | Auth status and current-user checks |
| `helpers.issues` | Create/edit/transition workflows |
| `helpers.search` | JQL issue search |
| `helpers.comments` | Comment list/add/update/delete |
| `helpers.changelogs` | Complete issue changelog retrieval and known-ID retrieval |
| `helpers.worklogs` | Worklog list/add/update/delete/report |
| `helpers.attachments` | Attachment list/read/plan/download/upload/delete |
| `helpers.metadata` | Transitions, projects, statuses, priorities, users, and field metadata |
| `helpers.links` | Issue-link list/types/create/delete |
| `helpers.filters` | Saved filter list/search/run |

## `HelperResult`

Helper methods return `HelperResult`.

```python
result = helpers.filters.run("12345", fields=["summary", "status"])

print(result.text)
print(result.data)
print(result.raw_content)
print(result.has_raw_output)
```

## Workflow examples

### Auth

```python
print(helpers.auth.status().text)
print(helpers.auth.me().text)
```

### Issues and transitions

```python
issue = api.issues.get_issue(
    "PROJ-123",
    fields=["summary", "status", "description"],
)
print(format_issue(issue, browse_url=f"{api.credentials.url}/browse/{issue['key']}"))
print(helpers.metadata.transitions("PROJ-123").text)
print(helpers.issues.transition("PROJ-123", "Done").text)
```

`format_issue` is pure: it does not fetch or mutate the issue. It shows only field keys Jira returned, so missing fields are omitted and present empty values remain visible.

### Changelogs

```python
# Retrieves all Jira changelog pages before returning one aggregate.
result = helpers.changelogs.list(
    "PROJ-123",
    created_at_or_after="2026-01-01T00:00:00Z",
    created_before="2026-02-01T00:00:00Z",
)
print(result.text)
print(result.data["changelogs"])

# Fetch known history IDs with one POST request. Order and duplicates are forwarded.
known = helpers.changelogs.list_by_ids("PROJ-123", [10001, 10002])
print(known.data["changelogs"])  # histories from Jira's PageOfChangelogs envelope
```

Date bounds are compared in UTC with inclusive lower and exclusive upper semantics. Filtering is local and runs only after the complete history has been retrieved. `result.data` remains `{"issue_key": ..., "changelogs": [...]}` with Jira's original history mappings; it never contains synthetic pagination fields. `list_by_ids()` likewise extracts the original mappings from the POST response's `histories` envelope and does not expose its page metadata. Entries without a usable `created` timestamp are retained without bounds and excluded when either bound is supplied.

### Comments

```python
helpers.comments.add("PROJ-123", "Followed up with the customer.")
helpers.comments.update("PROJ-123", "10001", "Updated note")
helpers.comments.delete("PROJ-123", "10001")
```

### Attachments

```python
print(helpers.attachments.list("PROJ-123").text)
print(helpers.attachments.read("10001").text)
print(helpers.attachments.plan_download("10001", output_path="downloads/").text)
print(helpers.attachments.download("10001", output_path="downloads/").text)
print(helpers.attachments.upload("PROJ-123", "./error.log").text)
```

### Worklogs

```python
print(helpers.worklogs.list("PROJ-123").text)
helpers.worklogs.add("PROJ-123", "1h", comment="Investigation")
helpers.worklogs.update("PROJ-123", "10010", time_spent="90m")
helpers.worklogs.delete("PROJ-123", "10010")
```

### Metadata, links, and filters

```python
print(helpers.metadata.project("PROJ").text)
print(helpers.metadata.statuses().text)
print(helpers.metadata.priorities().text)
print(helpers.links.list("PROJ-123").text)
print(helpers.filters.search("Team").text)
print(helpers.filters.run("12345").text)
```

`helpers.filters.run()` resolves the saved filter's JQL and returns the same search-style result shape as `helpers.search.issues()`.

## Helper errors

- `JiraHelperValidationError`
- `JiraHelperOperationError`
- `AttachmentError`
- `AttachmentDownloadError`

## Public vs private helper API

Supported public helper API includes:

- `JiraHelpers`
- grouped helper classes
- `HelperResult`
- `format_issue`
- documented helper errors and models

Not supported as public API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules

## See also

- [API Reference: High-level Helpers](../api/helpers.md)
- [Low-level JiraAPI](../api/jira-api.md)
