# High-level Helpers

`jira2py.helpers.JiraHelpers` is an optional high-level facade for common **Jira Cloud** workflows.

Use it when you want grouped operations plus readable `HelperResult` output instead of raw Jira REST payloads.

## Import path

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)
```

## Helper groups

```python
helpers.auth
helpers.issues
helpers.search
helpers.comments
helpers.worklogs
helpers.attachments
helpers.metadata
helpers.links
helpers.filters
```

| Group | Use for |
| --- | --- |
| `helpers.auth` | Auth status and current-user checks |
| `helpers.issues` | Read/create/edit/transition workflows |
| `helpers.search` | JQL issue search |
| `helpers.comments` | Comment list/add/update/delete |
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
print(helpers.issues.read("PROJ-123").text)
print(helpers.metadata.transitions("PROJ-123").text)
print(helpers.issues.transition("PROJ-123", "Done").text)
```

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
- documented helper errors and models

Not supported as public API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules

## See also

- [API Reference: High-level Helpers](../api/helpers.md)
- [Low-level JiraAPI](../api/jira-api.md)
