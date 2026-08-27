# High-level Helpers

`jira2py.helpers.JiraHelpers` is the public high-level helper facade for **Jira Cloud** workflows.

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)
```

## Facade groups

| Property | Helper class | Common methods |
| --- | --- | --- |
| `helpers.auth` | `AuthHelpers` | `status()`, `me()` |
| `helpers.issues` | `IssueHelpers` | `create()`, `edit()`, `transition()`, `validate_create()`, `validate_edit()` |
| `helpers.search` | `SearchHelpers` | `issues()` |
| `helpers.comments` | `CommentHelpers` | `list()`, `add()`, `update()`, `delete()` |
| `helpers.changelogs` | `ChangelogHelpers` | `list()`, `list_by_ids()` |
| `helpers.worklogs` | `WorklogHelpers` | `list()`, `add()`, `update()`, `delete()`, `report()` |
| `helpers.attachments` | `AttachmentHelpers` | `list()`, `read()`, `plan_download()`, `download()`, `upload()`, `delete()` |
| `helpers.metadata` | `MetadataHelpers` | `issue_types()`, `create_fields()`, `edit_fields()`, `transitions()`, `project()`, `projects()`, `statuses()`, `priorities()`, `users()` |
| `helpers.links` | `LinkHelpers` | `list()`, `types()`, `create()`, `delete()` |
| `helpers.filters` | `FiltersHelpers` | `list()`, `search()`, `run()` |

## Grouped usage

```python
helpers.auth.status()
helpers.issues.transition("PROJ-123", "Done")
helpers.comments.update("PROJ-123", "10001", "Updated note")
helpers.changelogs.list("PROJ-123")
helpers.worklogs.add("PROJ-123", "1h")
helpers.attachments.download("10001", output_path="downloads/")
helpers.metadata.statuses()
helpers.links.list("PROJ-123")
helpers.filters.run("12345")
```

## Structured issue reads and presentation

`IssueHelpers` does not retrieve full issues. Use the low-level endpoint as the sole retrieval authority, then optionally pass the returned mapping to public `format_issue`:

```python
from jira2py.helpers import format_issue

issue = api.issues.get_issue(
    "PROJ-123",
    fields=["summary", "status", "description"],
)
text = format_issue(
    issue,
    browse_url=f"{api.credentials.url}/browse/{issue['key']}",
)
```

`format_issue(data, *, browse_url=None)` is pure: it performs no I/O, does not change `data`, and does not choose or retrieve fields. It renders a known field only when that raw key exists in `data["fields"]`; a present empty value is shown truthfully, while an absent field is omitted. Existing `data["names"]` labels custom fields when supplied, but the formatter never requests names. ADF values are converted only for this text presentation.

## `HelperResult`

Most helper methods return `HelperResult`.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `text` | `str` | Human-readable helper output |
| `data` | `Any \| None` | Optional structured payload |
| `raw_content` | `str \| None` | Optional serialized raw output |
| `has_raw_output` | `bool` | Whether `data` or `raw_content` is present |

## Complete changelogs

`helpers.changelogs.list(issue_key, *, created_at_or_after=None, created_before=None)` retrieves every Jira changelog page from offset zero before returning. Its `HelperResult.data` is a helper-owned aggregate with no pagination fields:

```python
result = helpers.changelogs.list(
    "PROJ-123",
    created_at_or_after="2026-01-01T00:00:00Z",
    created_before="2026-02-01T00:00:00Z",
)
# {"issue_key": "PROJ-123", "changelogs": [...]}
```

Optional bounds are local ISO-8601 comparisons normalized to UTC: the lower bound is inclusive and the upper bound is exclusive (`created_at_or_after <= created < created_before`). Naive timestamps are treated as UTC. Filtering happens only after all pages have been retrieved; entries with a missing or unparseable `created` value remain when unfiltered and are excluded when either bound is supplied.

For known IDs, `helpers.changelogs.list_by_ids(issue_key, changelog_ids)` validates one non-empty sequence of integer IDs and performs one POST request. It extracts the original history mappings from Jira's `PageOfChangelogs` `histories` collection; request order and duplicates are retained, while the aggregate retains Jira's response order without exposing page metadata.

Malformed bounds and IDs raise `JiraHelperValidationError`. Request, response-shape, and non-progressing pagination failures raise `JiraHelperOperationError`; no partial aggregate is returned.

## Search continuation

`helpers.search.issues()` and `helpers.filters.run()` each make one enhanced-search request and return one raw Jira search page in `HelperResult.data`. When a page supplies `nextPageToken`, pass that opaque value unchanged to fetch the next page. Stop when no token is returned; do not use `total` as the completion condition.

Keep the same JQL and fields for every `helpers.search.issues()` call:

```python
jql = "project = PROJ ORDER BY created DESC"
fields = ["summary", "status", "assignee"]
issues = []
page = helpers.search.issues(jql, fields=fields)

while True:
    issues.extend(page.data["issues"])
    next_page_token = page.data.get("nextPageToken")
    if not next_page_token:
        break
    page = helpers.search.issues(
        jql,
        fields=fields,
        next_page_token=next_page_token,
    )
```

For a saved filter, repeat `helpers.filters.run()` with the same filter ID and fields:

```python
issues = []
page = helpers.filters.run("12345", fields=fields)
while True:
    issues.extend(page.data["issues"])
    next_page_token = page.data.get("nextPageToken")
    if not next_page_token:
        break
    page = helpers.filters.run(
        "12345",
        fields=fields,
        next_page_token=next_page_token,
    )
```

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
- `JiraChangelog`
- `JiraChangelogItem`
- `ChangelogPage`
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

- `create(project_key, issue_type, summary, *, description=None, fields=None)`
- `edit(issue_key, *, summary=None, description=None, fields=None, raw=False)`
- `transition(issue_key, transition)`
- `validate_create(...)`
- `validate_edit(...)`

### `helpers.search`

- `issues(jql, *, max_results=20, fields=None, next_page_token=None)`

### `helpers.changelogs`

- `list(issue_key, *, created_at_or_after=None, created_before=None)`
- `list_by_ids(issue_key, changelog_ids)`

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
- `run(filter_id, *, max_results=20, fields=None, next_page_token=None)`

`helpers.filters.run()` resolves the saved filter's JQL and delegates to the normal search pathway, so its structured output matches `helpers.search.issues()`.

## Public/private boundary

The following are intentionally **not** public helper API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules
- internal formatting and conversion behavior, except public `format_issue`

## See also

- [Guide: High-level Helpers](../guide/high-level-helpers.md)
- [Low-level JiraAPI](jira-api.md)
