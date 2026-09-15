# ADF Bridge API Reference

Import these APIs from `adf_bridge`, not from `jira2py`. This is a curated reference
for the locked `adf-bridge==0.1.3` release; ADF Bridge owns the full conversion
profile and diagnostics catalog.

## Functions

### `markdown_to_adf`

```python
markdown_to_adf(
    markdown: str,
    *,
    strict: bool = False,
    resolved_images: Sequence[ResolvedJiraImage] = (),
) -> ConversionResult[AdfDocument]
```

Converts portable GFM Markdown to the focused Jira ADF profile. In non-strict mode,
readable degradation is returned as ordered diagnostics. `strict=True` raises
`LossyConversionError` after a conversion that produced warnings; invalid or
out-of-profile input remains fatal in either mode.

### `adf_to_markdown`

```python
adf_to_markdown(
    document: AdfDocument,
    *,
    strict: bool = False,
) -> ConversionResult[str]
```

Validates and renders a focused ADF document as canonical portable GFM. It does not
promise an exact Markdown source round-trip.

### `markdown_image_urls`

```python
markdown_image_urls(
    markdown: str,
    *,
    strict: bool = False,
) -> ConversionResult[tuple[str, ...]]
```

Parses with the same focused profile as `markdown_to_adf` and returns supported image
destinations in source order. It neither fetches nor trusts those URLs.

### `validate_adf`

```python
validate_adf(document: AdfDocument) -> None
```

Validates an input document against ADF Bridge's fixed bundled schema. It does not
mutate the input, accept a caller-provided schema, or load plugins.

### `verify_jira_media_readback`

```python
verify_jira_media_readback(
    submitted: AdfDocument,
    persisted: AdfDocument,
    *,
    resolved_images: Sequence[ResolvedJiraImage],
) -> None
```

Checks that caller-resolved Jira file media remains at the expected submitted ADF
paths after the caller has written and read a document. It is structural readback
verification, not a whole-document equality or rendered-HTML assertion.

## Result, types, and errors

- `JsonValue` is the recursive JSON-compatible value type. `AdfDocument` is a
  `dict[str, JsonValue]` document mapping.
- `ConversionResult[T]` contains `value` and an ordered tuple of `Diagnostic`
  values in `diagnostics`.
- `Diagnostic` has stable `code`, `severity`, `path`, `keyword`, and `schema_path`
  fields. Its `message` is explanatory, not text-stable.
- `ResolvedJiraImage` supplies an exact `source_url`, `media_id`, and `collection`.
  Its optional `width` and `height` must be paired positive intrinsic dimensions.

| Error | Meaning |
| --- | --- |
| `AdfBridgeError` | Base class for package errors. |
| `AdfConversionError` | Valid input is outside the focused Jira/GFM profile. |
| `AdfSchemaError` | The bundled trusted schema cannot be used. |
| `AdfValidationError` | Input fails bundled-schema validation. |
| `JiraMediaVerificationError` | Persisted managed media differs at a verified path. |
| `LossyConversionError` | Strict mode rejects warnings that non-strict conversion returns. |

## Diagnostics and strict mode

Use diagnostics for machine-readable handling of readable degradation. Do not depend
on diagnostic message text.

```python
from adf_bridge import LossyConversionError, markdown_to_adf

result = markdown_to_adf("- [x] Shipped")
for diagnostic in result.diagnostics:
    print(diagnostic.code, diagnostic.severity, diagnostic.path)

try:
    markdown_to_adf("- [x] Shipped", strict=True)
except LossyConversionError as error:
    for diagnostic in error.diagnostics:
        print(diagnostic.code)
```

Strict mode escalates warnings after conversion. Schema-invalid or out-of-profile
input raises its project-owned error regardless of the `strict` setting. Jira2Py's
private helper adapters do not expose this strict/diagnostic interface.

## Validation

```python
from adf_bridge import AdfValidationError, validate_adf

invalid_document = {
    "type": "doc",
    "version": 1,
    "content": "not a node list",
}

try:
    validate_adf(invalid_document)
except AdfValidationError as error:
    print(error.path, error.keyword)
```

Validation uses ADF Bridge's fixed bundled schema and reports structured path/keyword
information where available. It is not a claim that every valid Atlassian ADF feature
is in the focused Markdown conversion profile.

## Images and readback

`ResolvedJiraImage` is caller-supplied data. ADF Bridge performs no Jira lookup,
upload, redirect handling, URL normalization, URL trust decision, or network access.
Exact parser-produced source URLs select Jira `file` media; unmapped images remain
external media and are not fetched.

```python
from adf_bridge import (
    ResolvedJiraImage,
    markdown_image_urls,
    markdown_to_adf,
    verify_jira_media_readback,
)

markdown = "![diagram](https://tenant.example.invalid/rest/api/3/attachment/content/10000)"
urls = markdown_image_urls(markdown)

resolution = ResolvedJiraImage(
    source_url=urls.value[0],
    media_id="caller-resolved-media-id",
    collection="",
    width=640,
    height=480,
)
submitted = markdown_to_adf(markdown, resolved_images=(resolution,)).value

# Offline stand-in only. After its own Jira write/read cycle, a caller supplies the
# raw persisted ADF mapping here instead; adf_bridge does not obtain it.
persisted = submitted
verify_jira_media_readback(submitted, persisted, resolved_images=(resolution,))
```

Mappings with invalid, duplicate, or unused values fail. Readback verifies the
resolved managed media at expected paths, not all ADF content. Jira2Py's managed-image
resolution is private integration behavior; use direct ADF Bridge calls only when your
application owns the resolution data.

## Upstream details

For exhaustive support, diagnostic, and schema/security details, use the reviewed
versioned upstream material rather than treating this page as a complete ADF reference:

- [ADF Bridge v0.1.3 source](https://github.com/en-ver/adf-bridge/tree/v0.1.3)
- [Upstream API reference](https://github.com/en-ver/adf-bridge/blob/v0.1.3/docs/api.md)
- [Support matrix](https://github.com/en-ver/adf-bridge/blob/v0.1.3/docs/support-matrix.md)
- [Diagnostics guide](https://github.com/en-ver/adf-bridge/blob/v0.1.3/docs/diagnostics.md)
- [Schema and security](https://github.com/en-ver/adf-bridge/blob/v0.1.3/docs/schema-and-security.md)
- [PyPI release](https://pypi.org/project/adf-bridge/0.1.3/)
