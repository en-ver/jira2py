# High-level Helpers

`jira2py.helpers.JiraHelpers` is the public high-level helper facade for jira2py.

Import it from `jira2py.helpers`, not top-level `jira2py`:

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)
```

`JiraAPI` remains the unchanged low-level REST facade. `JiraHelpers` builds grouped workflow helpers on top of it.

## Facade groups

| Property | Helper class | Common methods |
|---|---|---|
| `helpers.issues` | `IssueHelpers` | `read()`, `create()`, `edit()`, `validate_create()`, `validate_edit()` |
| `helpers.search` | `SearchHelpers` | `issues()` |
| `helpers.comments` | `CommentHelpers` | `list()`, `add()` |
| `helpers.worklogs` | `WorklogHelpers` | `report()` |
| `helpers.attachments` | `AttachmentHelpers` | `validate_id()`, `plan_download()` |
| `helpers.metadata` | `MetadataHelpers` | `issue_types()`, `create_fields()`, `edit_fields()`, `projects()`, `users()` |
| `helpers.links` | `LinkHelpers` | `types()`, `create()`, `delete()` |

## Grouped usage

```python
helpers.issues.read("PROJ-123")
helpers.search.issues("project = PROJ")
helpers.comments.list("PROJ-123")
helpers.worklogs.report(
    start_date="2026-01-01",
    end_date="2026-01-31",
    jql="project = PROJ",
)
helpers.attachments.plan_download("10001", output_path="downloads/")
helpers.metadata.issue_types("PROJ")
helpers.links.types()
```

## `HelperResult`

Most helper methods return `HelperResult`.

| Attribute | Type | Meaning |
|---|---|---|
| `text` | `str` | Human-readable helper output |
| `data` | `Any \| None` | Optional structured data payload |
| `raw_content` | `str \| None` | Optional serialized raw output |
| `has_raw_output` | `bool` | Whether `data` or `raw_content` is present |

High-level helpers are designed for workflow-oriented usage:

```python
result = helpers.search.issues("project = PROJ")
print(result.text)

if result.data:
    print(result.data["issues"][0]["key"])
```

## Helper errors

Public helper errors include:

- `JiraHelperError`
- `JiraHelperValidationError`
- `JiraHelperConfigError`
- `JiraHelperOperationError`
- `AttachmentError`
- `AttachmentDownloadError`

Use helper-layer errors for high-level workflow handling, and low-level `jira2py` exceptions when you are calling `JiraAPI` directly.

## Public models

Common public helper data models include:

- `AttachmentDownloadPlan`
- `AttachmentMeta`
- `FieldMeta`
- `FieldSchema`
- `IssueType`
- `JiraComment`
- `JiraIssue`
- `JiraProject`
- `JiraUser`
- `ProjectSearchResult`
- `SearchResult`
- `WorklogIssueSelector`
- `WorklogReport`
- `WorklogReportRow`

These models describe structured helper outputs. They do not replace the low-level Jira REST response shapes returned by `JiraAPI`.

## Group reference

### `helpers.issues`

High-level issue workflows that produce readable issue summaries and handle Markdown-to-ADF conversion internally when needed.

- `read(issue_key, *, extra_fields=None)`
- `create(project_key, issue_type, summary, *, description=None, fields=None)`
- `edit(issue_key, *, summary=None, description=None, fields=None, raw=False)`
- `validate_create(...)`
- `validate_edit(...)`

### `helpers.search`

Workflow-oriented JQL search with formatted output.

- `issues(jql, *, max_results=20, fields=None)`

### `helpers.comments`

Readable comment listing plus comment creation.

- `list(issue_key, *, start_at=0, max_results=50, order_by="created")`
- `add(issue_key, body)`

### `helpers.worklogs`

Cross-issue worklog reporting over issues selected by JQL.

- `report(*, start_date, end_date, jql, account_id=None, max_issues=100, include_details=False)`

### `helpers.attachments`

Attachment validation and generic download planning.

- `validate_id(attachment_id)`
- `plan_download(attachment_id, *, output_path=None, max_download=...)`

This layer does not publish wrapper-specific download safety policies as public API.

### `helpers.metadata`

Discovery helpers for issue types, create/edit field metadata, projects, and users.

- `issue_types(project_key)`
- `create_fields(project_key, issue_type)`
- `edit_fields(issue_key)`
- `projects(query=None)`
- `users(query, *, max_results=10)`

### `helpers.links`

Issue-link workflows.

- `types()`
- `create(link_type, outward_issue_key, inward_issue_key)`
- `delete(link_id)`

## Public/private boundary

The following are intentionally **not** public helper API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules
- internal formatting and conversion behavior

jira2py may continue to use internal ADF conversion and text formatting, but those implementation details are not a compatibility promise.

## See also

- [Guide: High-level Helpers](../guide/high-level-helpers.md)
- [Low-level JiraAPI](jira-api.md)
