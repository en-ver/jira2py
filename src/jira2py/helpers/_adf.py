"""Internal ADF conversion helpers for jira2py helper operations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from adf_bridge import (
    AdfBridgeError,
    AdfDocument,
    ResolvedJiraImage,
)
from adf_bridge import (
    adf_to_markdown as _adf_to_markdown,
)
from adf_bridge import (
    markdown_to_adf as _markdown_to_adf,
)

_ADF_SYSTEM_FIELDS: set[str] = {"description", "environment"}
_ADF_CUSTOM_SUFFIX = ":textarea"


def adf_to_markdown(adf: Any) -> str:
    """Convert an ADF document into Markdown text for readable presentation."""
    if not adf or not isinstance(adf, dict):
        return "(none)"

    try:
        return _adf_to_markdown(adf).value
    except AdfBridgeError:
        return _extract_text_fallback(adf)


def markdown_to_adf(
    markdown: str,
    *,
    resolved_images: Sequence[ResolvedJiraImage] = (),
) -> AdfDocument:
    """Convert Markdown into an ADF document."""
    if not markdown or not markdown.strip():
        return {"type": "doc", "version": 1, "content": []}
    return _markdown_to_adf(markdown, resolved_images=resolved_images).value


def is_adf_value(value: Any) -> bool:
    """Return whether a value looks like an ADF document."""
    return isinstance(value, dict) and value.get("type") == "doc"


def is_adf_field(field_id: str, custom_schema: str = "") -> bool:
    """Return whether a field is known to use ADF format."""
    if field_id in _ADF_SYSTEM_FIELDS:
        return True
    return bool(custom_schema and _ADF_CUSTOM_SUFFIX in custom_schema)


def convert_adf_values(data: dict[str, Any]) -> dict[str, Any]:
    """Convert any ADF values in a mapping to Markdown strings."""
    return {
        key: adf_to_markdown(value) if is_adf_value(value) else value
        for key, value in data.items()
    }


def detect_adf_field_ids(fields_metadata: list[dict[str, Any]]) -> set[str]:
    """Build a set of field ids that use ADF format."""
    adf_ids = set(_ADF_SYSTEM_FIELDS)
    for field in fields_metadata:
        field_id = field.get("id", "")
        schema = field.get("schema", {}) or {}
        custom = schema.get("custom", "")
        if custom and _ADF_CUSTOM_SUFFIX in custom:
            adf_ids.add(field_id)
    return adf_ids


def convert_markdown_fields(
    fields: dict[str, Any],
    adf_field_ids: set[str],
) -> dict[str, Any]:
    """Convert Markdown strings to ADF for known ADF-backed fields."""
    return {
        key: markdown_to_adf(value)
        if key in adf_field_ids and isinstance(value, str)
        else value
        for key, value in fields.items()
    }


def _extract_text_fallback(adf: dict[str, Any]) -> str:
    """Extract plain text from ADF as a last resort."""
    texts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text" and "text" in node:
                texts.append(node["text"])
            for child in node.get("content", []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(adf)
    return " ".join(texts).strip() or "(none)"
