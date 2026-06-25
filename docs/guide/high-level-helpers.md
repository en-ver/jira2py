# High-level Helpers

`jira2py.helpers.JiraHelpers` is an optional high-level facade for common Jira workflows.

Use it when you want readable helper output and grouped workflows such as `helpers.issues.read(...)` or `helpers.worklogs.report(...)`.

Keep using [`JiraAPI`](../api/jira-api.md) when you want direct access to low-level Jira REST endpoints and raw Jira response shapes.

## Import path

Import helpers from `jira2py.helpers`, not top-level `jira2py`:

```python
from jira2py import JiraAPI
from jira2py.helpers import JiraHelpers

api = JiraAPI()
helpers = JiraHelpers(api)
```

`JiraAPI` is unchanged. `JiraHelpers` simply composes an existing `JiraAPI` instance.

## Helper groups

```python
helpers.issues
helpers.search
helpers.comments
helpers.worklogs
helpers.attachments
helpers.metadata
helpers.links
```

| Group | Use for |
|---|---|
| `helpers.issues` | Readable issue read/create/edit workflows |
| `helpers.search` | JQL-based issue search workflows |
| `helpers.comments` | Listing and adding comments |
| `helpers.worklogs` | Cross-issue worklog reporting |
| `helpers.attachments` | Attachment validation and download planning |
| `helpers.metadata` | Issue types, field metadata, projects, and users |
| `helpers.links` | Link types and issue-link operations |

## `HelperResult`

Helper methods return `HelperResult` instead of raw Jira REST payloads.

```python
result = helpers.issues.read("PROJ-123")

print(result.text)          # readable summary
print(result.data)          # optional structured data
print(result.raw_content)   # optional serialized raw output
print(result.has_raw_output)
```

At a high level:

- `text` is meant for humans
- `data` is for structured post-processing
- `raw_content` is optional extra raw output when a helper has it

If you want only raw Jira endpoint responses, call the low-level `JiraAPI` methods directly.

## Workflow examples

### Issues and search

```python
issue = helpers.issues.read("PROJ-123")
print(issue.text)

search = helpers.search.issues(
    "project = PROJ AND statusCategory != Done ORDER BY updated DESC"
)
print(search.text)
```

### Comments

```python
comments = helpers.comments.list("PROJ-123")
print(comments.text)

helpers.comments.add("PROJ-123", "Followed up with the customer.")
```

### Worklogs

```python
report = helpers.worklogs.report(
    start_date="2026-01-01",
    end_date="2026-01-31",
    jql="project = PROJ",
    account_id="557058:example",
)
print(report.text)
```

### Attachments

```python
plan = helpers.attachments.plan_download(
    "10001",
    output_path="downloads/",
)
print(plan.text)
```

The helper layer currently plans attachment output destinations and validates attachment metadata. Wrapper-specific filesystem safety policies remain outside the public helper API.

### Metadata

```python
issue_types = helpers.metadata.issue_types("PROJ")
create_fields = helpers.metadata.create_fields("PROJ", "Task")
edit_fields = helpers.metadata.edit_fields("PROJ-123")
projects = helpers.metadata.projects("Platform")
users = helpers.metadata.users("alex@example.com")
```

### Links

```python
link_types = helpers.links.types()
print(link_types.text)

helpers.links.create("Blocks", "PROJ-123", "PROJ-456")
helpers.links.delete("10000")
```

## Helper errors

Helper validation and operation failures use helper-specific exceptions:

- `JiraHelperValidationError` — invalid helper input before a Jira API call
- `JiraHelperOperationError` — failure while performing the underlying Jira operation
- `AttachmentError` / `AttachmentDownloadError` — attachment-specific failures

```python
from jira2py.helpers import JiraHelperOperationError, JiraHelperValidationError

try:
    helpers.issues.edit("PROJ-123")
except JiraHelperValidationError as exc:
    print(f"Invalid helper input: {exc.message}")
except JiraHelperOperationError as exc:
    print(f"Jira operation failed: {exc.message}")
```

Helpers preserve the original exception as `__cause__` when they wrap lower-level failures.

## Public vs private helper API

Supported public helper API includes:

- `from jira2py.helpers import JiraHelpers`
- grouped helper classes
- `HelperResult`
- documented helper errors and models

Not supported as public API:

- `jira2py.helpers._adf`
- `jira2py.helpers._text`
- other private `_*.py` helper modules
- internal conversion or formatting details

Those internals may change without compatibility guarantees.

## See also

- [API Reference: High-level Helpers](../api/helpers.md)
- `examples/high_level_helpers.py` in the repository
