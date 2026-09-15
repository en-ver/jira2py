"""Public ADF Bridge dependency and documentation contract."""

from __future__ import annotations

import inspect
import re
import tomllib
from collections.abc import Callable
from importlib import metadata
from pathlib import Path

import adf_bridge

import jira2py
import jira2py.helpers

PROJECT_ROOT = Path(__file__).parent.parent
API_PAGE = PROJECT_ROOT / "docs" / "adf-bridge" / "api.md"
OVERVIEW_PAGE = PROJECT_ROOT / "docs" / "adf-bridge" / "index.md"
_REQUIRED = object()
_REVIEWED_REQUIREMENT = "adf-bridge>=0.1.3,<0.2"
_REVIEWED_VERSION = "0.1.3"

_REVIEWED_EXPORTS = {
    "AdfBridgeError",
    "AdfConversionError",
    "AdfDocument",
    "AdfSchemaError",
    "AdfValidationError",
    "ConversionResult",
    "Diagnostic",
    "JiraMediaVerificationError",
    "JsonValue",
    "LossyConversionError",
    "ResolvedJiraImage",
    "adf_to_markdown",
    "markdown_image_urls",
    "markdown_to_adf",
    "validate_adf",
    "verify_jira_media_readback",
}

_CALLABLE_SHAPES = {
    "adf_to_markdown": (
        ("document", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),
        ("strict", inspect.Parameter.KEYWORD_ONLY, False),
    ),
    "markdown_image_urls": (
        ("markdown", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),
        ("strict", inspect.Parameter.KEYWORD_ONLY, False),
    ),
    "markdown_to_adf": (
        ("markdown", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),
        ("strict", inspect.Parameter.KEYWORD_ONLY, False),
        ("resolved_images", inspect.Parameter.KEYWORD_ONLY, ()),
    ),
    "validate_adf": (("document", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),),
    "verify_jira_media_readback": (
        ("submitted", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),
        ("persisted", inspect.Parameter.POSITIONAL_OR_KEYWORD, _REQUIRED),
        ("resolved_images", inspect.Parameter.KEYWORD_ONLY, _REQUIRED),
    ),
}


def _adf_bridge_requirement() -> str:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    matches = [
        dependency
        for dependency in project["project"]["dependencies"]
        if dependency.startswith("adf-bridge")
    ]
    assert len(matches) == 1
    return matches[0]


def _locked_adf_bridge_version() -> str:
    lock = tomllib.loads((PROJECT_ROOT / "uv.lock").read_text())
    matches = [
        package for package in lock["package"] if package["name"] == "adf-bridge"
    ]
    assert len(matches) == 1
    return matches[0]["version"]


def _parameters(
    function: Callable[..., object],
) -> tuple[tuple[str, inspect._ParameterKind, object], ...]:
    return tuple(
        (
            parameter.name,
            parameter.kind,
            _REQUIRED
            if parameter.default is inspect.Parameter.empty
            else parameter.default,
        )
        for parameter in inspect.signature(function).parameters.values()
    )


def _quickstart_code(page: str) -> str:
    quickstart = page.split("## Quickstart", maxsplit=1)[1]
    match = re.search(r"```python\n(.*?)\n```", quickstart, re.DOTALL)
    assert match is not None
    return match.group(1)


def test_adf_bridge_dependency_and_public_docs_contract() -> None:
    requirement = _adf_bridge_requirement()
    locked_version = _locked_adf_bridge_version()
    overview = OVERVIEW_PAGE.read_text()
    api_page = API_PAGE.read_text()

    assert requirement == _REVIEWED_REQUIREMENT
    assert locked_version == _REVIEWED_VERSION
    assert metadata.version("adf-bridge") == locked_version
    assert requirement in overview
    assert f"adf-bridge=={locked_version}" in overview

    assert set(adf_bridge.__all__) == _REVIEWED_EXPORTS
    for name, expected_shape in _CALLABLE_SHAPES.items():
        function = getattr(adf_bridge, name)
        assert _parameters(function) == expected_shape
        return_annotation = str(inspect.signature(function).return_annotation)
        if name in {"validate_adf", "verify_jira_media_readback"}:
            assert return_annotation == "None"
        else:
            assert return_annotation.startswith("ConversionResult[")

    for export in _REVIEWED_EXPORTS:
        assert export in api_page

    expected_links = {
        f"https://github.com/en-ver/adf-bridge/tree/v{locked_version}",
        f"https://github.com/en-ver/adf-bridge/blob/v{locked_version}/docs/api.md",
        f"https://github.com/en-ver/adf-bridge/blob/v{locked_version}/docs/support-matrix.md",
        f"https://github.com/en-ver/adf-bridge/blob/v{locked_version}/docs/diagnostics.md",
        f"https://github.com/en-ver/adf-bridge/blob/v{locked_version}/docs/schema-and-security.md",
        f"https://pypi.org/project/adf-bridge/{locked_version}/",
    }
    assert all(link in overview + api_page for link in expected_links)

    namespace: dict[str, object] = {}
    exec(  # noqa: S102 - executes the repository-controlled documentation quickstart
        compile(_quickstart_code(overview), str(OVERVIEW_PAGE), "exec"), namespace
    )
    assert {"created", "document", "rendered"}.issubset(namespace)

    bridge_exports = set(adf_bridge.__all__)
    assert bridge_exports.isdisjoint(jira2py.__all__)
    assert bridge_exports.isdisjoint(jira2py.helpers.__all__)
    for export in bridge_exports:
        assert not hasattr(jira2py, export)
        assert not hasattr(jira2py.helpers, export)
