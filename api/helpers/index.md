# High-level Helpers

`jira2py.helpers.JiraHelpers` is the public high-level helper facade for **Jira Cloud** workflows.

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)
```

## Facade groups

| Property              | Helper class        | Common methods                                                                                                                           |
| --------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `helpers.auth`        | `AuthHelpers`       | `status()`, `me()`                                                                                                                       |
| `helpers.issues`      | `IssueHelpers`      | `read()`, `create()`, `edit()`, `transition()`, `validate_create()`, `validate_edit()`                                                   |
| `helpers.search`      | `SearchHelpers`     | `issues()`                                                                                                                               |
| `helpers.comments`    | `CommentHelpers`    | `list()`, `add()`, `update()`, `delete()`                                                                                                |
| `helpers.worklogs`    | `WorklogHelpers`    | `list()`, `add()`, `update()`, `delete()`, `report()`                                                                                    |
| `helpers.attachments` | `AttachmentHelpers` | `list()`, `read()`, `plan_download()`, `download()`, `upload()`, `delete()`                                                              |
| `helpers.metadata`    | `MetadataHelpers`   | `issue_types()`, `create_fields()`, `edit_fields()`, `transitions()`, `project()`, `projects()`, `statuses()`, `priorities()`, `users()` |
| `helpers.links`       | `LinkHelpers`       | `list()`, `types()`, `create()`, `delete()`                                                                                              |
| `helpers.filters`     | `FiltersHelpers`    | `list()`, `search()`, `run()`                                                                                                            |

## Grouped usage

```python
helpers.auth.status()
helpers.issues.transition("PROJ-123", "Done")
helpers.comments.update("PROJ-123", "10001", "Updated note")
helpers.worklogs.add("PROJ-123", "1h")
helpers.attachments.download("10001", output_path="downloads/")
helpers.metadata.statuses()
helpers.links.list("PROJ-123")
helpers.filters.run("12345")
```

## `HelperResult`

Most helper methods return `HelperResult`.

| Attribute        | Type          | Meaning                                    |
| ---------------- | ------------- | ------------------------------------------ |
| `text`           | `str`         | Human-readable helper output               |
| `data`           | `Any \| None` | Optional structured payload                |
| `raw_content`    | `str \| None` | Optional serialized raw output             |
| `has_raw_output` | `bool`        | Whether `data` or `raw_content` is present |

## Helper errors

Public helper errors include:

- `JiraHelperError`
- `JiraHelperValidationError`
- `JiraHelperConfigError`
- `JiraHelperOperationError`
- `AttachmentError`
- `AttachmentDownloadError`

## Public models

Common public helper models include:

- `AttachmentDownloadPlan`
- `AttachmentMeta`
- `FilterSearchResult`
- `IssueTransition`
- `IssueType`
- `JiraComment`
- `JiraIssue`
- `JiraPriority`
- `JiraProject`
- `JiraStatus`
- `JiraUser`
- `JiraWorklog`
- `ProjectSearchResult`
- `SearchResult`
- `WorklogPage`
- `WorklogReport`
- `WorklogReportRow`

## Group reference

### `helpers.auth`

- `status()`
- `me()`

### `helpers.issues`

- `read(issue_key, *, extra_fields=None)`
- `create(project_key, issue_type, summary, *, description=None, fields=None)`
- `edit(issue_key, *, summary=None, description=None, fields=None, raw=False)`
- `transition(issue_key, transition)`
- `validate_create(...)`
- `validate_edit(...)`

### `helpers.search`

- `issues(jql, *, max_results=20, fields=None)`

### `helpers.comments`

- `list(issue_key, *, start_at=0, max_results=50, order_by="created")`
- `add(issue_key, body)`
- `update(issue_key, comment_id, body)`
- `delete(issue_key, comment_id)`

### `helpers.worklogs`

- `list(issue_key, *, start_at=0, max_results=50)`
- `add(issue_key, time_spent, *, started=None, comment=None)`
- `update(issue_key, worklog_id, *, time_spent=None, started=None, comment=None)`
- `delete(issue_key, worklog_id)`
- `report(*, start_date, end_date, jql, account_id=None, max_issues=100, include_details=False)`

### `helpers.attachments`

- `list(issue_key)`
- `read(attachment_id)`
- `plan_download(attachment_id, *, output_path=None, max_download=...)`
- `download(attachment_id, *, output_path=None, max_download=...)`
- `upload(issue_key, file_path)`
- `delete(attachment_id)`

### `helpers.metadata`

- `issue_types(project_key)`
- `create_fields(project_key, issue_type)`
- `edit_fields(issue_key)`
- `transitions(issue_key)`
- `project(project_id_or_key)`
- `projects(query=None)`
- `statuses()`
- `priorities()`
- `users(query, *, max_results=10)`

### `helpers.links`

- `list(issue_key)`
- `types()`
- `create(link_type, outward_issue_key, inward_issue_key)`
- `delete(link_id)`

### `helpers.filters`

- `list(*, start_at=0, max_results=50)`
- `search(query, *, start_at=0, max_results=50)`
- `run(filter_id, *, max_results=20, fields=None)`

`helpers.filters.run()` resolves the saved filter's JQL and delegates to the normal search pathway, so its structured output matches `helpers.search.issues()`.

## Public/private boundary

The following are intentionally **not** public helper API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules
- internal formatting and conversion behavior

## See also

- [Guide: High-level Helpers](https://jira2py.org/guide/high-level-helpers/index.md)
- [Low-level JiraAPI](https://jira2py.org/api/jira-api/index.md)
