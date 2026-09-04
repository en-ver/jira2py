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

| Group                 | Use for                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------- |
| `helpers.auth`        | Auth status and current-user checks                                                         |
| `helpers.issues`      | Create/edit/transition workflows                                                            |
| `helpers.search`      | JQL issue search                                                                            |
| `helpers.comments`    | Comment list/add/update/delete                                                              |
| `helpers.changelogs`  | Complete issue changelog retrieval and known-ID retrieval                                   |
| `helpers.worklogs`    | Worklog list/add/update/delete/report                                                       |
| `helpers.attachments` | Attachment list/read/plan/download/upload/delete                                            |
| `helpers.metadata`    | Field catalog, create/edit metadata, transitions, projects, statuses, priorities, and users |
| `helpers.links`       | Issue-link list/types/create/delete                                                         |
| `helpers.filters`     | Saved filter list/search/run                                                                |

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

### Jira account mentions

High-level Markdown write helpers recognize Jira account mentions as `[~accountId:<account-id>]`. Obtain the opaque account ID through Jira user discovery; do not substitute a display name. This syntax applies to issue create/edit descriptions, `environment`, compatible custom textarea fields, comment add/update bodies, and worklog add/update comments:

```python
helpers.comments.add("PROJ-123", "Please review [~accountId:557057:User:AbC]")
```

The `accountId` label is case-insensitive on input, and IDs can contain `:`. A single leading backslash escapes a token; malformed tokens and tokens inside Markdown code, links, or images remain ordinary text rather than creating mentions. Jira may notify the mentioned account where supported; jira2py does not guarantee notification delivery.

Formatted issue, comment, and worklog ADF output is presentation-only: pyadf renders mention display text rather than the account ID. Mention identity may be lost if that formatted text is edited and written back through a high-level Markdown helper. For identity-safe edits, retrieve and submit raw ADF with the low-level API until dedicated formatted read/edit/write support is available. Raw ADF in `HelperResult.data` and low-level API responses is unchanged. Native transition `fields` and `update` mappings are also unchanged and are not Markdown-converted.

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

- [API Reference: High-level Helpers](https://jira2py.org/api/helpers/index.md)
- [Low-level JiraAPI](https://jira2py.org/api/jira-api/index.md)
