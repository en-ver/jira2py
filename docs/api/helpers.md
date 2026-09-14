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
| `helpers.attachments` | `AttachmentHelpers` | `list()`, `read()`, `download()`, `upload()`, `delete()` |
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
helpers.attachments.download("10001", directory="downloads/")
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
mentions. Bold, italic, and strikethrough wrappers around a valid mention create an
unmarked Jira mention, so that formatting is discarded. Jira may notify mentioned
accounts where supported; notification delivery is not guaranteed.

Formatted issue, comment, and worklog ADF output presents mentions with adf-bridge's
identity-preserving `[~accountId:<account-id>]` token; a mention's display text is not
retained. jira2py does not traverse mentions or rewrite the rendered Markdown, so
literal matching tokens, including code spans, remain literal. Raw ADF in low-level
responses and `HelperResult.data` remains untouched. Native
transition `fields` and `update` mappings are forwarded unchanged and do not receive
Markdown conversion.

## Jira-managed Markdown images

Use an associated upload's ordinary `content` URL in native Markdown, for example
`![Screenshot](https://tenant.atlassian.net/rest/api/3/attachment/content/10000)`.
High-level issue **edit** rich fields (`description`, `environment`, and metadata-detected
textarea fields), comment add/update bodies, and worklog add/update comments recognize
only that exact configured-Jira HTTPS form without a query or fragment delimiter,
including bare `?` or `#`. The attachment must belong to the target issue and be
`image/*`; external and relative images stay external.

The helpers replace complete field or body values, not append fragments. Issue creation
rejects both canonical and malformed same-site attachment-content image destinations:
create first, upload to the returned key, then edit the full rich-text field with the
upload result's `content` URL. Markdown image titles are not preserved.

Before a managed write, jira2py acquires dimensions privately from the authenticated Jira
attachment endpoint. A no-follow `redirect=false` 64-byte range probe handles PNG/APNG,
GIF, WebP, and BMP; JPEG and TIFF, and any inconclusive probe, use one complete fallback
when its reported attachment size is at most 100 MiB. JPEG/TIFF EXIF orientation is
applied. Dimensions must be positive, at most 65,535 per axis, and at most 89,478,485
pixels. The parser inspects metadata only and does not prove that every pixel decodes.
Unsupported, malformed, oversized-for-fallback, or protocol-invalid content fails before
the mutation. A supported large image found in the prefix does not need a full download.
Each helper mutation acquires each unique attachment once and retains no attachment bytes.

Managed media is centered with a 100% parent width and exact intrinsic child dimensions.
External and relative images remain widthless external media and are never fetched.
Formatted ADF reads cannot recover the managed attachment-content URL; use raw ADF when
that structure matters. Successful managed-media writes verify raw persisted ADF
structure; rendered HTML is not a runtime verification contract and needs authorized
live end-to-end corroboration for a specific tenant.

After dimensions are acquired, jira2py validates Jira's currently observed no-follow
`303` Media Services redirect shape. This is compatibility-sensitive behavior, not a
public Jira mapping API. `download_attachment_content()` remains the separate public
bounded streaming operation and continues to follow redirects. A direct issue, comment, or
worklog mutation that fails with a connection error or Jira 5xx may already have been
applied; the helper error sets `details["mutation_may_have_succeeded"]`, and callers must
reread before retrying. jira2py does not retry or roll back after that uncertain failure.

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

## Create metadata pagination

`helpers.metadata.issue_types(project_key)` makes one low-level create-issue-types request at offset zero with the low-level default page size of 50. Its `data` contains only that response page's `values` list (or `issueTypes` fallback); Jira page metadata is discarded.

`helpers.metadata.create_fields(project_key, issue_type)` resolves the case-insensitive issue-type name from only that same first issue-type page. An issue type that Jira places on a later page can therefore be reported as absent. After resolution, it makes one create-fields request at offset zero with the same low-level default page size of 50 and returns only that page's `values` list (or `fields` fallback), again without page metadata. Neither high-level bare list has a continuation mechanism.

For complete discovery, call the low-level methods page by page and inspect each raw Jira page envelope:

```python
types_page = api.issues.get_create_issue_types(
    "PROJ", start_at=0, max_results=50
)
fields_page = api.issues.get_create_fields(
    "PROJ", "10001", start_at=0, max_results=50
)
# Advance start_at while inspecting each page's Jira metadata.
```

## Project pagination

`helpers.metadata.projects(query=None)` trims a supplied query and makes one project-search request at Jira's default offset, requesting up to 100 entries ordered by name. `HelperResult.data` is Jira's unchanged first-page envelope. Its text notes that more projects exist when Jira reports that condition, but the helper has no continuation argument.

For more pages, use the low-level offset controls with the same ordering:

```python
page = api.projects.search_projects(
    start_at=100,
    max_results=100,
    query="backend",
    extra_params={"orderBy": "name"},
)
```

## Transition discovery and execution

`helpers.metadata.transitions(issue_key, *, transition_id=None, include_unavailable_transitions=None)` always requests `expand="transitions.fields"`. Its structured `data` is the complete raw Jira transitions envelope; the concise text lists transition IDs, destination status IDs/names, availability, screen/conditional/global/looped indicators, and transition-screen field keys/names/requirements/operations. Schema, allowed/default values, autocomplete URLs, configuration, and unknown members remain Jira-native in `data`.

Use `transition_id` to inspect one selected transition. Set `include_unavailable_transitions=True` only for diagnostics: it includes informational unavailable entries but does not make them executable.

`helpers.issues.transition(issue_key, transition, *, fields=None, update=None)` accepts a transition ID or, for compatibility, a name. Prefer an ID obtained from fresh discovery. `fields` and `update` are passed as Jira-native mappings; the helper rejects exact field-key overlap but does not locally validate required fields, schemas, allowed values, or operations. `historyMetadata` and issue properties intentionally remain low-level `jira.issues.transition_issue()` parameters.

Its successful `HelperResult.data` retains the existing transition result keys and adds `verified: false`. Jira accepted the request, but the expected destination is not an observed result and no verification read is performed. Submitted `fields` and `update` bodies are not included in the result.

## Issue edits

`helpers.issues.edit(issue_key, *, summary=None, description=None, fields=None, raw=False)` treats empty `summary` and `description` values as absent. If they are the only supplied update values, validation reports “Nothing to update.” The `fields` mapping cannot contain `summary` or `description`, so this helper cannot express an explicit description clear.

With the default `raw=False`, the helper calls the low-level edit endpoint with `return_issue=False` and returns text only: `HelperResult.data` and `raw_content` are both absent. With `raw=True`, it requests `return_issue=True`; a returned issue mapping becomes `HelperResult.data`, while an empty or no-content response produces `raw_content="null"` and no `data`. `raw=True` does not itself perform a separate verification read; managed-media verification is a distinct behavior.

To send Jira an explicit JSON null for a description, use the low-level method instead:

```python
api.issues.edit_issue(
    "PROJ-123",
    fields={"description": None},
)
```

This sends JSON null in the Jira request. jira2py does not promise how any particular tenant will persist or present that value.

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

## Worklog reports

`helpers.worklogs.report(*, start_date, end_date, jql, account_id=None, max_issues=100, include_details=False)` accepts strict `YYYY-MM-DD` dates interpreted in UTC. Both named dates are inclusive: structured output records the interval as inclusive `startedAtOrAfter` and exclusive `startedBefore` at midnight after `end_date`.

The issue search stops after `max_issues`. Before treating report totals as complete, inspect `data["issueSelector"]["truncated"]`: when it is true, `rows`, `rowCount`, `totalSeconds`, and `totalHours` cover only scanned issues. `nextPageToken` can establish truncation, and a known `total` can establish it even without a token. For every selected issue, the helper pages through worklogs and retains only entries whose parseable `started` timestamp lies in the UTC interval.

`account_id` is an exact author account-ID filter. Every row always includes the detail fields `updateAuthor`, `visibility`, `comment`, and `properties`; `include_details=True` populates them without changing date or author inclusion, while `False` leaves them null. Core result fields are `rowCount`, `totalSeconds`, `totalHours`, `rows`, and `issueSelector`; rows are ordered lexicographically by the returned/formatted `started` string, then issue key and worklog ID. Differing fractional-second precision means that order is not reliably chronological.

## Search continuation

`helpers.search.issues()` and `helpers.filters.run()` each make one enhanced-search request and return one raw Jira search page in `HelperResult.data`. The high-level default `fields=None` still requests exactly:

```python
[
    "summary",
    "status",
    "assignee",
    "priority",
    "issuetype",
    "created",
    "updated",
]
```

`max_results` defaults to 20, and values above 50 are silently reduced to 50. `helpers.filters.run()` resolves the saved JQL and delegates to `helpers.search.issues()`, so it has the same projection and cap. This intentionally differs from low-level `api.search.enhanced_search()`, where `fields=None` omits the field selection. When a page supplies `nextPageToken`, pass that opaque value unchanged to fetch the next page. Stop when no token is returned; do not use `total` as the completion condition.

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

Helper errors are independent of the low-level [`JiraError`](exceptions.md#jiraerror) hierarchy and are imported from `jira2py.helpers`:

```text
JiraHelperError
├── JiraHelperValidationError
├── JiraHelperConfigError
├── JiraHelperOperationError
└── AttachmentError
    └── AttachmentDownloadError
```

`JiraHelperError` does not inherit from `JiraError`. Local credential, input, and response checks can also raise built-in `ValueError` or `TypeError`; parsing helper models can raise model-validation errors.

## Public models

Common public helper models include:

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

`status()` converts a failure raised by the current-user endpoint into `HelperResult.data` with `ok=False`. It is not a universal no-raise guarantee: unrelated post-response processing can still raise.

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
- `download(attachment_id, *, directory=".", filename=None, max_download=100 * 1024 * 1024)`

`download()` defaults to exactly 100 MiB (104,857,600 bytes). `max_download` must be a positive integer and can be overridden. It validates the attachment ID, limit, directory, and any explicit filename before metadata lookup. If valid Jira metadata reports a size above the limit, it raises `AttachmentError` before content transfer or final-path replacement.

The helper resolves and owns the destination directory. An explicit `filename` must be a safe basename; otherwise Jira metadata is sanitized to one. It streams to a same-directory temporary file and atomically replaces the final entry only after success. When metadata has no `size`, the cumulative streaming cap still applies. Transfer or protocol failures are wrapped as `AttachmentDownloadError`; failed high-level transfers remove the temporary file and do not replace the final destination. Its data contains status, attachment ID, filename, absolute output file, observed size, and MIME type.
- `upload(issue_key, file_path)`
- `delete(attachment_id)`

### `helpers.metadata`

- `list_fields(project_key=None, *, query=None, field_ids=None, field_types=None, start_at=0, max_results=20)`
- `issue_types(project_key)` — first create-issue-types page only; see [Create metadata pagination](#create-metadata-pagination)
- `create_fields(project_key, issue_type)` — first issue-type and create-fields pages only; see [Create metadata pagination](#create-metadata-pagination)
- `edit_fields(issue_key)`
- `transitions(issue_key, *, transition_id=None, include_unavailable_transitions=None)`
- `project(project_id_or_key)`
- `projects(query=None)` — requests up to 100 entries ordered by name and returns Jira's unchanged first-page envelope; see [Project pagination](#project-pagination)
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

`helpers.filters.run()` resolves the saved filter's JQL and delegates to the normal search pathway, so its structured output, default projection, page-size cap, and continuation behavior match `helpers.search.issues()`.

## Public/private boundary

The following are intentionally **not** public helper API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` modules
- internal formatting and conversion behavior, except public `format_issue`

## See also

- [Guide: High-level Helpers](../guide/high-level-helpers.md)
- [Low-level JiraAPI](jira-api.md)
