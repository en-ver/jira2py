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
| `helpers.attachments` | Attachment list/read/download/upload/delete |
| `helpers.metadata` | Field catalog, create/edit metadata, transitions, projects, statuses, priorities, and users |
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

`helpers.auth.status()` turns a failure from the current-user endpoint into `HelperResult.data` with `ok=False`; inspect that flag. It is not a universal no-raise guarantee, because unrelated post-response processing can still raise.

### Issues and transitions

```python
issue = api.issues.get_issue(
    "PROJ-123",
    fields=["summary", "status", "description"],
)
print(format_issue(issue, browse_url=f"{api.credentials.url}/browse/{issue['key']}"))

metadata = helpers.metadata.transitions("PROJ-123")
print(metadata.text)
print(metadata.data)  # complete Jira transitions envelope with transitions.fields

accepted = helpers.issues.transition(
    "PROJ-123",
    "31",  # use a transition ID from fresh discovery
    fields={"resolution": {"name": "Done"}},
    update={"labels": [{"add": "released"}]},
)
print(accepted.text)
assert accepted.data["verified"] is False

# Explicit verification read; transition() does not perform one automatically.
observed = api.issues.get_issue("PROJ-123", fields=["status", "resolution", "labels"])
```

`helpers.metadata.transitions()` always requests `transitions.fields`. Its `data` remains Jira's complete, unchanged transitions envelope, including field schema, allowed/default values, autocomplete URLs, configuration, and unfamiliar members. Its text identifies each transition and destination status IDs/names, availability and workflow indicators, and field keys/names/requirements/operations. Use `transition_id="31"` for focused discovery or `include_unavailable_transitions=True` only for diagnostics; an unavailable transition is not executable.

`helpers.issues.transition()` accepts Jira-native `fields` and `update` mappings unchanged. The same exact field key cannot occur in both mappings; Jira remains responsible for required fields, schemas, allowed values, and field operations. The helper accepts transition names for compatibility, but IDs are preferred because names may be ambiguous. It does not expose history metadata or entity properties; use low-level `api.issues.transition_issue()` for those Jira capabilities.

A successful transition helper result means Jira accepted the request, not that the destination was observed. It explicitly reports `verified: false`, describes the destination as expected, and never includes submitted request bodies. Read the issue explicitly when verification matters.

`format_issue` is pure: it does not fetch or mutate the issue. It shows only field keys Jira returned, so missing fields are omitted and present empty values remain visible.

For `helpers.issues.edit()`, the default `raw=False` produces text only; it does not provide `data` or `raw_content`. With `raw=True`, Jira's returned issue mapping is `data`; an empty response instead has `raw_content="null"`. Empty `summary` and `description` are omitted, and the helper rejects those keys in `fields`, so it cannot clear a description. To send Jira JSON null, use the low-level API:

```python
api.issues.edit_issue("PROJ-123", fields={"description": None})
```

That request does not promise tenant-specific persisted presentation. `raw=True` does not itself add a verification read; managed-media verification is separate.

### Jira account mentions

High-level Markdown write helpers recognize Jira account mentions as
`[~accountId:<account-id>]`. Obtain the opaque account ID through Jira user discovery;
do not substitute a display name. This syntax applies to issue create/edit descriptions,
`environment`, compatible custom textarea fields, comment add/update bodies, and
worklog add/update comments:

```python
helpers.comments.add("PROJ-123", "Please review [~accountId:557057:User:AbC]")
```

The `accountId` label is case-insensitive on input, and IDs can contain `:`. A single
leading backslash escapes a token; malformed tokens and tokens inside Markdown code,
links, or images remain ordinary text rather than creating mentions. Bold, italic, and
strikethrough wrappers around a valid mention create an unmarked Jira mention, so that
formatting is discarded. Jira may notify the mentioned account where supported;
jira2py does not guarantee notification delivery.

Formatted issue, comment, and worklog ADF output presents mentions with adf-bridge's
identity-preserving `[~accountId:<account-id>]` token; a mention's display text is not
retained. jira2py does not traverse mentions or rewrite the rendered Markdown, so
literal matching tokens, including code spans, remain literal. Raw ADF in
`HelperResult.data` and low-level API responses is unchanged. Native
transition `fields` and `update` mappings are also unchanged and are not
Markdown-converted.

### Jira-managed Markdown images

After uploading an image, use the upload item's `content` URL in ordinary Markdown:

```python
upload = helpers.attachments.upload("PROJ-123", "screen.png")
helpers.comments.add("PROJ-123", f"![Failure screen]({upload.data[0]['content']})")
```

The same automatic managed-media conversion applies to issue **edit** `description`,
`environment`, and compatible custom textarea fields, and to comment and worklog
add/update bodies. It accepts only exact configured-Jira HTTPS attachment-content URLs
for attachments associated with the target issue and marked `image/*`, with no query or
fragment delimiter, including bare `?` or `#`. External and relative image URLs remain
external. Every high-level write replaces the full field or body value, so submit the
complete desired Markdown, not an append fragment.

Issue create cannot use an attachment-content image URL because there is no issue yet.
Create the issue, upload the image to the returned issue key, then edit the complete
rich-text field with the upload result's `content` URL. Markdown image titles are not
preserved.

Before a managed write, jira2py obtains intrinsic dimensions only through the authenticated
Jira attachment endpoint. It sends a no-follow `redirect=false` 64-byte range probe for
PNG/APNG, GIF, WebP, and BMP, then makes one full fallback for JPEG, TIFF, or an
inconclusive probe only when the reported attachment size is at most 100 MiB. JPEG/TIFF
EXIF orientation is applied. Dimensions must be positive, no more than 65,535 per axis,
and no more than 89,478,485 pixels. This metadata inspection is not full pixel decoding.
Malformed, unsupported, oversized-for-fallback, and protocol-invalid content fails before
the mutation. A supported large image that succeeds from the prefix is not rejected for
requiring a full download. One helper mutation acquires each unique attachment once and
does not retain attachment bytes.

Managed media is centered with a 100% parent width and exact intrinsic child dimensions.
External and relative images remain widthless external media and are never fetched.
Managed ADF media has no recoverable attachment URL on formatted Markdown reads; use raw
ADF when exact Jira media structure matters. Successful managed-media writes verify raw
persisted ADF structure. Jira-rendered HTML is not a runtime verification contract;
corroborate tenant rendering with authorized live end-to-end testing.

After dimensions are acquired, the internal no-follow `303` redirect validation checks
Jira's current observed Media Services redirect shape. It is compatibility-sensitive
rather than a public Jira mapping API. Public attachment downloads stream with a required
byte cap; the managed-media reader remains separate. If a direct issue, comment, or worklog mutation fails with a connection error
or Jira 5xx, it may already have been applied. Its helper error sets
`details["mutation_may_have_succeeded"]`; callers must reread before retrying. jira2py
does not retry or roll back after that uncertain failure.

### Changelogs

```python
# Retrieves all Jira changelog pages before returning one aggregate.
result = helpers.changelogs.list(
    "PROJ-123",
    created_at_or_after="2026-01-01T00:00:00Z",
    created_before="2026-02-01T00:00:00Z",
    field_ids=["summary", "customfield_10001"],
    result_max_results=20,
)
print(result.text)
print(result.data["changelogs"])

# Fetch known history IDs with one POST request. Order and duplicates are forwarded.
known = helpers.changelogs.list_by_ids("PROJ-123", [10001, 10002])
print(known.data["changelogs"])  # histories from Jira's PageOfChangelogs envelope
```

Date bounds are compared in UTC with inclusive lower and exclusive upper semantics. Filtering is local and runs only after the complete history has been retrieved. `field_ids` matches raw `item["fieldId"]` exactly and case-sensitively, never the display `field`; it prunes unmatched items and events with no remaining items while preserving all other raw properties, nulls, and Jira order. Entries without a usable `created` timestamp are retained without bounds and excluded when either bound is supplied.

`result_max_results` enables post-filter event pagination. All Jira changelog pages are still fetched first, then timestamps and field IDs are applied before the event slice. A paged result adds helper-owned `result_page` metadata (`start_at`, `max_results`, filtered-event `total`, `is_last`, and `next_start_at`); omit result pagination to retain the existing `{"issue_key": ..., "changelogs": [...]}` envelope exactly. `list_by_ids()` accepts the same `field_ids` filter but never adds result pagination; it extracts the original mappings from the POST response's `histories` envelope.

### Comments

```python
helpers.comments.add("PROJ-123", "Followed up with the customer.")
helpers.comments.update("PROJ-123", "10001", "Updated note")
helpers.comments.delete("PROJ-123", "10001")
```

### Search and saved filters

`helpers.search.issues()` and `helpers.filters.run()` return one raw enhanced-search page. Their default `fields=None` requests exactly `summary`, `status`, `assignee`, `priority`, `issuetype`, `created`, and `updated`; it does not omit fields. Both default to 20 results and silently cap larger values at 50. Continue with the opaque `nextPageToken` while keeping the JQL and fields unchanged. `filters.run()` resolves saved JQL and delegates to the same search path. Use low-level `api.search.enhanced_search()` when `fields=None` must be omitted.

### Attachments

```python
print(helpers.attachments.list("PROJ-123").text)
print(helpers.attachments.read("10001").text)
result = helpers.attachments.download(
    "10001", directory="downloads/", filename="report.csv"
)
print(result.text)
print(result.data["output_file"])  # absolute path; size is observed bytes
print(helpers.attachments.upload("PROJ-123", "./error.log").text)
```

`download()` defaults to 100 MiB (104,857,600 bytes). Its positive-integer `max_download` limit is overrideable and applies both to a known metadata size before transfer and cumulatively while streaming when size is absent. It writes a temporary file and replaces the final path only after success; failures clean up the temporary file and raise `AttachmentDownloadError` for transfer/protocol failures.

### Worklogs

```python
print(helpers.worklogs.list("PROJ-123").text)
helpers.worklogs.add("PROJ-123", "1h", comment="Investigation")
helpers.worklogs.update("PROJ-123", "10010", time_spent="90m")
helpers.worklogs.delete("PROJ-123", "10010")

report = helpers.worklogs.report(
    start_date="2026-01-01",
    end_date="2026-01-31",
    jql="project = PROJ",
)
if report.data["issueSelector"]["truncated"]:
    print("Totals cover only scanned issues")
```

`report()` uses strict UTC `YYYY-MM-DD` dates and includes both named dates. It pages worklogs for each selected issue and filters parseable `started` timestamps to that UTC interval. Rows are ordered lexicographically by the returned/formatted `started` string, then issue key and worklog ID; differing fractional-second precision means this is not reliably chronological. `max_issues` limits issue search, so inspect `issueSelector.truncated` before treating `rowCount`, `totalSeconds`, or `totalHours` as complete. `account_id` is an exact author account-ID filter; every row always includes update author, visibility, comment, and properties, which `include_details=True` populates and `False` leaves null without changing inclusion.

### Metadata, links, and filters

```python
field_page = helpers.metadata.list_fields(
    "PROJ",
    query="points",
    field_types=["custom"],
)
print(field_page.text)  # display names plus canonical field IDs
print(field_page.data["values"])

print(helpers.metadata.project("PROJ").text)
print(helpers.metadata.statuses().text)
print(helpers.metadata.priorities().text)
print(helpers.links.list("PROJ-123").text)
print(helpers.filters.search("Team").text)
print(helpers.filters.run("12345").text)
```

`helpers.metadata.list_fields()` returns one raw Jira `/field/search` page. A project key is resolved to Jira's numeric project ID and passed as a project-context filter. Jira documents this endpoint for Classic projects; it has no issue-type or screen-applicability guarantee. Use `create_fields()` and `edit_fields()` when you need create-screen or existing-issue edit metadata.

`helpers.metadata.issue_types()` aggregates official create-issue-type pages into an ordered bare list of raw mappings. `create_fields()` scans official issue-type pages in Jira order until the first case-insensitive match with a nonblank raw ID, stops that lookup immediately, then aggregates official create-field pages. Both preserve raw mappings and unknown item properties without returning a page envelope. Each helper page requires its operation's `issueTypes` or `fields` collection plus valid non-negative `startAt` and `total`; present `maxResults` is validated. Continuation uses the returned offset and current-page total, while `values` and `isLast` are ignored rather than treated as create-metadata controls. Historical metadata-free and `values`/`isLast`-only mock forms are rejected. Use the low-level `api.issues.get_create_issue_types()` and `api.issues.get_create_fields()` with `start_at`/`max_results` only when you need individual raw page envelopes.

`helpers.metadata.projects()` trims its optional query, requests up to 100 entries ordered by name, and returns Jira's unchanged first project-search page envelope. Its text can signal more results, but it has no continuation argument; use `api.projects.search_projects(start_at=..., max_results=..., query=..., extra_params={"orderBy": "name"})` to continue.

`helpers.filters.run()` resolves the saved filter's JQL and returns the same search-style result shape as `helpers.search.issues()`.

## Helper errors

Helper errors are independent of the low-level `JiraError` hierarchy and are imported from `jira2py.helpers`:

```text
JiraHelperError
├── JiraHelperValidationError
├── JiraHelperConfigError
├── JiraHelperOperationError
└── AttachmentError
    └── AttachmentDownloadError
```

`JiraHelperError` does not inherit from `JiraError`. Local credential, input, and response checks can raise built-in `ValueError` or `TypeError`, and helper model parsing can raise model-validation errors.

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
