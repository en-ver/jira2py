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
| `helpers.metadata` | `MetadataHelpers` | `list_fields()`, `issue_types()`, `create_fields()`, `edit_fields()`, `transitions()`, `project()`, `projects()`, `statuses()`, `priorities()`, `users()` |
| `helpers.links` | `LinkHelpers` | `list()`, `types()`, `create()`, `delete()` |
| `helpers.filters` | `FiltersHelpers` | `list()`, `search()`, `run()` |

## Grouped usage

```python
helpers.auth.status()
helpers.issues.transition("PROJ-123", "31")
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

## Jira account mentions

High-level Markdown write methods recognize `[~accountId:<account-id>]` for issue
create/edit descriptions, `environment`, compatible custom textarea fields, comment
add/update bodies, and worklog add/update comments. Use a Jira-discovered opaque
account ID, not a display name. Input accepts case-insensitive `accountId`, including
IDs containing `:`. A single leading backslash escapes a token; malformed tokens and
tokens inside Markdown code, links, or images remain ordinary text rather than creating
mentions. Jira may notify mentioned accounts where supported; notification delivery is
not guaranteed.

Formatted issue, comment, and worklog ADF output is presentation-only: pyadf renders
mention display text rather than the account ID. Mention identity may be lost if that
formatted text is edited and written back through a high-level Markdown helper. For
identity-safe edits, retrieve and submit raw ADF with the low-level API until dedicated
formatted read/edit/write support is available. Raw ADF in low-level responses and
`HelperResult.data` remains untouched. Native transition `fields` and `update` mappings
are forwarded unchanged and do not receive Markdown conversion.

## `HelperResult`

Most helper methods return `HelperResult`.

| Attribute | Type | Meaning |
| --- | --- | --- |
| `text` | `str` | Human-readable helper output |
| `data` | `Any \| None` | Optional structured payload |
| `raw_content` | `str \| None` | Optional serialized raw output |
| `has_raw_output` | `bool` | Whether `data` or `raw_content` is present |

## Field catalog

`helpers.metadata.list_fields(project_key=None, *, query=None, field_ids=None, field_types=None, start_at=0, max_results=20)` returns one raw Jira `/field/search` page in `HelperResult.data`. The values and Jira page metadata remain unchanged, while `text` is a concise list of display names and canonical `id` values:

```python
result = helpers.metadata.list_fields(
    "PROJ",
    query="points",
    field_ids=["customfield_10001"],
    field_types=["custom"],
    start_at=0,
    max_results=20,
)
# {"startAt": 0, "maxResults": 20, "total": 1, "isLast": True,
#  "values": [{"id": "customfield_10001", "name": "Story Points", ...}]}
```

A supplied project key is resolved once to Jira's numeric project ID before the field search. `query` is trimmed, and a blank query is omitted. Canonical field IDs are exact, unpadded strings with no commas; `field_types` accepts only `"system"` and `"custom"`; `start_at` must be non-negative and `max_results` positive. These inputs are validated before Jira requests.

This is Jira's `/field/search` **project-context** filter, documented for Classic Jira projects. It has no issue-type parameter and does not establish create-screen or edit-screen applicability. Continue to use `create_fields()` for a project's create-screen metadata and `edit_fields()` for an existing issue's edit metadata.

## Transition discovery and execution

`helpers.metadata.transitions(issue_key, *, transition_id=None, include_unavailable_transitions=None)` always requests `expand="transitions.fields"`. Its structured `data` is the complete raw Jira transitions envelope; the concise text lists transition IDs, destination status IDs/names, availability, screen/conditional/global/looped indicators, and transition-screen field keys/names/requirements/operations. Schema, allowed/default values, autocomplete URLs, configuration, and unknown members remain Jira-native in `data`.

Use `transition_id` to inspect one selected transition. Set `include_unavailable_transitions=True` only for diagnostics: it includes informational unavailable entries but does not make them executable.

`helpers.issues.transition(issue_key, transition, *, fields=None, update=None)` accepts a transition ID or, for compatibility, a name. Prefer an ID obtained from fresh discovery. `fields` and `update` are passed as Jira-native mappings; the helper rejects exact field-key overlap but does not locally validate required fields, schemas, allowed values, or operations. `historyMetadata` and issue properties intentionally remain low-level `jira.issues.transition_issue()` parameters.

Its successful `HelperResult.data` retains the existing transition result keys and adds `verified: false`. Jira accepted the request, but the expected destination is not an observed result and no verification read is performed. Submitted `fields` and `update` bodies are not included in the result.

## Complete changelogs

`helpers.changelogs.list(issue_key, *, created_at_or_after=None, created_before=None, field_ids=None, result_start_at=0, result_max_results=None)` retrieves every Jira changelog page from offset zero before applying local filters. With result pagination omitted, its `HelperResult.data` is the existing helper-owned aggregate with no pagination fields:

```python
result = helpers.changelogs.list(
    "PROJ-123",
    created_at_or_after="2026-01-01T00:00:00Z",
    created_before="2026-02-01T00:00:00Z",
)
# {"issue_key": "PROJ-123", "changelogs": [...]}
```

Optional bounds are local ISO-8601 comparisons normalized to UTC: the lower bound is inclusive and the upper bound is exclusive (`created_at_or_after <= created < created_before`). Naive timestamps are treated as UTC. Filtering happens only after all pages have been retrieved; entries with a missing or unparseable `created` value remain when unfiltered and are excluded when either bound is supplied.

`field_ids` filters each retained event's raw `items` by exact, case-sensitive `item["fieldId"]`. It never falls back to display `field`; absent or null `fieldId` values do not match. Retained events and items keep their raw properties, nulls, and Jira order; events with no matching items are removed. Omit `field_ids` to preserve the existing unfiltered mappings and behavior.

Supplying `result_max_results` enables local event pagination after timestamps, field-item filtering, and removal of empty events. Jira's complete history is still fetched first. The result then includes `result_page` with `start_at`, `max_results`, filtered-event `total`, `is_last`, and `next_start_at`; this helper-owned metadata is absent when result pagination is omitted. `result_start_at` requires `result_max_results`.

For known IDs, `helpers.changelogs.list_by_ids(issue_key, changelog_ids, *, field_ids=None)` validates one non-empty sequence of integer IDs and performs one POST request. It applies the same field-item filtering, retains request duplicates and Jira response order, and extracts raw histories from Jira's `PageOfChangelogs` collection without adding result pagination.

Malformed bounds, IDs, field IDs, and result pagination inputs raise `JiraHelperValidationError`. Request, response-shape, and non-progressing pagination failures raise `JiraHelperOperationError`; no partial aggregate is returned.

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
- `transition(issue_key, transition, *, fields=None, update=None)`
- `validate_create(...)`
- `validate_edit(...)`

### `helpers.search`

- `issues(jql, *, max_results=20, fields=None, next_page_token=None)`

### `helpers.changelogs`

- `list(issue_key, *, created_at_or_after=None, created_before=None, field_ids=None, result_start_at=0, result_max_results=None)`
- `list_by_ids(issue_key, changelog_ids, *, field_ids=None)`

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

- `list_fields(project_key=None, *, query=None, field_ids=None, field_types=None, start_at=0, max_results=20)`
- `issue_types(project_key)`
- `create_fields(project_key, issue_type)`
- `edit_fields(issue_key)`
- `transitions(issue_key, *, transition_id=None, include_unavailable_transitions=None)`
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
