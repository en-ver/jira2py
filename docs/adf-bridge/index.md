# ADF Bridge

[ADF Bridge](https://github.com/en-ver/adf-bridge/tree/v0.1.3) is a separate,
focused library for converting portable GFM Markdown and a Jira-oriented subset of
Atlassian Document Format (ADF). Its distribution name is `adf-bridge`; its Python
import name is `adf_bridge`.

Jira2Py currently declares `adf-bridge>=0.1.3,<0.2`, and this repository's lock
selects `adf-bridge==0.1.3`. These pages were reviewed against that locked release
and describe its focused v0.1 profile. Upstream classifies v0.1.3 as Alpha;
standalone applications should choose and declare their own version policy. ADF
Bridge owns its converter semantics, diagnostics, and support profile; Atlassian owns
ADF and Jira persistence/rendering behavior. Jira2Py documents only its integration
boundary.

## Install for direct use

A standalone application that converts Markdown or ADF should declare ADF Bridge as
a **direct dependency**. Do not rely on Jira2Py installing it transitively.

=== "pip"

    ```bash
    python -m pip install adf-bridge
    ```

=== "uv"

    ```bash
    uv add adf-bridge
    ```

Jira2Py does not re-export `adf_bridge` or provide a Jira2Py conversion runtime API.

## Quickstart

ADF Bridge is pure conversion and validation code: this example does not contact Jira
or any other service.

```python
from adf_bridge import adf_to_markdown, markdown_to_adf, validate_adf

source = "## Release\n\nHello **world**."

created = markdown_to_adf(source)
document = created.value
validate_adf(document)

rendered = adf_to_markdown(document)
print(document["type"])
print(rendered.value)
print(created.diagnostics, rendered.diagnostics)
```

`value` is an ordinary JSON-compatible dictionary or string. Rendered Markdown is
canonical portable GFM, so exact source spelling is not a round-trip contract. See
[API Reference](api.md) for diagnostics, strict mode, validation, and media handling.

## Choose a layer

| Need | Use |
| --- | --- |
| Conversion, validation, diagnostics, or strict behavior without Jira | Import `adf_bridge` directly. |
| Raw Jira REST payload control | Build an ADF mapping with `adf_bridge` and supply it to a low-level `JiraAPI` rich-text field. |
| Convenience Markdown writes and readable helper output | Use `JiraHelpers`; see [High-level Helpers](../guide/high-level-helpers.md). |

For example, direct callers who need strict conversion keep control of the result and
can later supply its `value` to a low-level Jira API call of their choice:

```python
from adf_bridge import markdown_to_adf

body = markdown_to_adf("Hello **world**", strict=True).value
# Supply `body` to a low-level JiraAPI ADF parameter only when making a Jira request.
```

## Jira2Py integration boundary

Low-level Jira2Py APIs accept caller-supplied ADF mappings for rich-text values. The
high-level helpers instead use private adapters for Markdown issue descriptions,
`environment`, metadata-detected textarea fields, comment add/update bodies, and
worklog add/update comments. Raw ADF field values and helper transition `fields` /
`update` mappings bypass that Markdown conversion. `format_issue` and formatted
comment/worklog helper text render ADF only for presentation.

Those private adapters are intentionally not the direct ADF Bridge API:

- blank Markdown is special-cased to an empty-content ADF document;
- conversion diagnostics and `strict` are not exposed through helpers;
- write-side bridge failures become helper validation errors; and
- presentation catches bridge errors and falls back to readable plain text.

Use direct `adf_bridge` calls when those diagnostics, strict behavior, or the exact
focused conversion contract matter. Jira2Py's private managed-media resolution is an
integration detail, not a standalone image-resolution API.

## Upstream authority

This tab is a curated reference, not a replacement for ADF Bridge's upstream
documentation. Consult the versioned [ADF Bridge v0.1.3 source](https://github.com/en-ver/adf-bridge/tree/v0.1.3)
for the release itself, and the [API Reference](api.md) for links to its exhaustive
support, diagnostics, and schema documentation.
