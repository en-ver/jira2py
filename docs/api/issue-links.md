# Issue Links

Accessed via `jira.issue_links`. List available link types, create links between issues, and delete existing links.

## `get_link_types`

Get all available issue link types.

```python
result = jira.issue_links.get_link_types()

for link_type in result["issueLinkTypes"]:
    print(f"{link_type['name']}: {link_type['inward']} / {link_type['outward']}")
```

This method takes no parameters.

**Returns:** `dict[str, Any]` — dictionary with `issueLinkTypes` containing link type objects.

:link: [Jira REST API — Get issue link types](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-link-types/#api-rest-api-3-issuelinktype-get)

---

## `create_link`

Create a link between two issues.

```python
# "PROJ-1 blocks PROJ-2"
jira.issue_links.create_link("Blocks", "PROJ-1", "PROJ-2")

# "PROJ-3 is cloned by PROJ-4"
jira.issue_links.create_link("Cloners", "PROJ-3", "PROJ-4")
```

Use [`get_link_types`](#get_link_types) to discover available link type names.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `link_type_name` | `str` | required | Link type name (e.g., `"Blocks"`, `"Cloners"`, `"Duplicate"`) |
| `inward_issue_key` | `str` | required | Key of the inward issue |
| `outward_issue_key` | `str` | required | Key of the outward issue |

**Returns:** `None`

:link: [Jira REST API — Create issue link](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-post)

---

## `delete_link`

Delete an issue link. The link ID can be found in the `issuelinks` field of an issue.

```python
issue = jira.issues.get_issue("PROJ-123", fields="issuelinks")

for link in issue["fields"]["issuelinks"]:
    print(f"Link {link['id']}: {link['type']['name']}")

# Delete a specific link
jira.issue_links.delete_link("10001")
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `link_id` | `str` | required | ID of the issue link to delete |

**Returns:** `None`

:link: [Jira REST API — Delete issue link](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-links/#api-rest-api-3-issuelink-linkid-delete)
