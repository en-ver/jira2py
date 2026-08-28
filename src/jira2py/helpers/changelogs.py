"""Grouped changelog helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from jira2py.api import JiraAPI

from ._text import format_changelog_list
from ._validation import (
    parse_iso_datetime,
    require_non_empty_string,
    validate_canonical_field_ids,
)
from .errors import JiraHelperOperationError, JiraHelperValidationError
from .models import ChangelogPage, JiraChangelog
from .results import HelperResult


class ChangelogHelpers:
    """High-level complete-history and known-ID changelog retrieval helpers."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def list(
        self,
        issue_key: str,
        *,
        created_at_or_after: str | None = None,
        created_before: str | None = None,
        field_ids: Sequence[str] | None = None,
        result_start_at: int = 0,
        result_max_results: int | None = None,
    ) -> HelperResult:
        """Retrieve every changelog page, then apply local result filters."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        lower_bound = _parse_bound(
            created_at_or_after,
            field_name="created_at_or_after",
        )
        upper_bound = _parse_bound(
            created_before,
            field_name="created_before",
        )
        if (
            lower_bound is not None
            and upper_bound is not None
            and upper_bound < lower_bound
        ):
            raise JiraHelperValidationError(
                "created_before must be on or after created_at_or_after."
            )
        field_ids = validate_canonical_field_ids(field_ids)
        result_start_at, result_max_results = _validate_result_pagination(
            result_start_at,
            result_max_results,
        )

        raw_changelogs: list[Mapping[str, Any]] = []
        changelogs: list[JiraChangelog] = []
        start_at = 0

        while True:
            try:
                data = self.api.issues.get_changelogs(
                    issue_id=issue_key,
                    start_at=start_at,
                )
            except Exception as exc:
                raise JiraHelperOperationError(
                    f"Failed to fetch changelogs for {issue_key}: {exc}"
                ) from exc

            page, raw_values = _parse_page(data)
            raw_changelogs.extend(raw_values)
            changelogs.extend(page.values)

            if page.isLast:
                break

            next_start = page.startAt + len(raw_values)
            if next_start <= start_at:
                raise JiraHelperOperationError(
                    "Jira returned a non-final changelog page that did not advance."
                )
            start_at = next_start

        selected_raw, selected_changelogs = _filter_changelogs(
            raw_changelogs,
            changelogs,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        selected_raw, selected_changelogs = _filter_changelogs_by_field_ids(
            selected_raw,
            selected_changelogs,
            field_ids=field_ids,
        )
        if result_max_results is None:
            return _result(issue_key, selected_raw, selected_changelogs)

        page_raw, page_changelogs, result_page = _page_result(
            selected_raw,
            selected_changelogs,
            start_at=result_start_at,
            max_results=result_max_results,
        )
        return _result(
            issue_key,
            page_raw,
            page_changelogs,
            result_page=result_page,
        )

    def list_by_ids(
        self,
        issue_key: str,
        changelog_ids: Sequence[int],
        *,
        field_ids: Sequence[str] | None = None,
    ) -> HelperResult:
        """Retrieve the changelog histories identified by known Jira IDs."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        ids = _validate_changelog_ids(changelog_ids)
        field_ids = validate_canonical_field_ids(field_ids)

        try:
            data = self.api.issues.get_changelogs_by_ids(
                issue_id=issue_key,
                changelog_ids=ids,
            )
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch changelogs for {issue_key}: {exc}"
            ) from exc

        raw_changelogs, changelogs = _parse_changelog_histories(data)
        selected_raw, selected_changelogs = _filter_changelogs_by_field_ids(
            raw_changelogs,
            changelogs,
            field_ids=field_ids,
        )
        return _result(issue_key, selected_raw, selected_changelogs)


def _parse_bound(value: str | None, *, field_name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise JiraHelperValidationError(f"{field_name} must be an ISO-8601 timestamp.")

    parsed = parse_iso_datetime(value)
    if parsed is None:
        raise JiraHelperValidationError(f"{field_name} must be an ISO-8601 timestamp.")
    return parsed


def _validate_changelog_ids(changelog_ids: Sequence[int]) -> list[int]:
    if isinstance(changelog_ids, (str, bytes, bytearray)) or not isinstance(
        changelog_ids, Sequence
    ):
        raise JiraHelperValidationError(
            "changelog_ids must be a non-empty sequence of integers."
        )
    if not changelog_ids:
        raise JiraHelperValidationError("changelog_ids must not be empty.")
    if any(
        not isinstance(changelog_id, int) or isinstance(changelog_id, bool)
        for changelog_id in changelog_ids
    ):
        raise JiraHelperValidationError("changelog_ids must contain only integers.")
    return list(changelog_ids)


def _parse_page(data: object) -> tuple[ChangelogPage, list[Mapping[str, Any]]]:
    if not isinstance(data, Mapping):
        raise JiraHelperOperationError("Jira returned a malformed changelog page.")
    page_data = cast(Mapping[str, Any], data)
    start_at = page_data.get("startAt")
    if not isinstance(start_at, int) or isinstance(start_at, bool) or start_at < 0:
        raise JiraHelperOperationError("Jira returned a malformed changelog page.")
    if not isinstance(page_data.get("isLast"), bool):
        raise JiraHelperOperationError("Jira returned a malformed changelog page.")

    raw_values = page_data.get("values")
    raw_changelogs = _validate_raw_changelogs(raw_values)
    try:
        page = ChangelogPage.model_validate(page_data)
    except Exception as exc:
        raise JiraHelperOperationError(
            "Jira returned a malformed changelog page."
        ) from exc
    return page, raw_changelogs


def _parse_changelog_histories(
    data: object,
) -> tuple[list[Mapping[str, Any]], list[JiraChangelog]]:
    if not isinstance(data, Mapping):
        raise JiraHelperOperationError("Jira returned malformed changelog data.")
    page_data = cast(Mapping[str, Any], data)
    raw_changelogs = _validate_raw_changelogs(page_data.get("histories"))
    try:
        changelogs = [
            JiraChangelog.model_validate(changelog) for changelog in raw_changelogs
        ]
    except Exception as exc:
        raise JiraHelperOperationError(
            "Jira returned malformed changelog data."
        ) from exc
    return raw_changelogs, changelogs


def _validate_raw_changelogs(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not all(
        isinstance(changelog, Mapping) for changelog in value
    ):
        raise JiraHelperOperationError("Jira returned malformed changelog data.")
    return cast(list[Mapping[str, Any]], value)


def _filter_changelogs(
    raw_changelogs: list[Mapping[str, Any]],
    changelogs: list[JiraChangelog],
    *,
    lower_bound: datetime | None,
    upper_bound: datetime | None,
) -> tuple[list[Mapping[str, Any]], list[JiraChangelog]]:
    if lower_bound is None and upper_bound is None:
        return raw_changelogs, changelogs

    selected_raw: list[Mapping[str, Any]] = []
    selected_changelogs: list[JiraChangelog] = []
    for raw_changelog, changelog in zip(raw_changelogs, changelogs, strict=True):
        created = parse_iso_datetime(changelog.created)
        if created is None:
            continue
        if lower_bound is not None and created < lower_bound:
            continue
        if upper_bound is not None and created >= upper_bound:
            continue
        selected_raw.append(raw_changelog)
        selected_changelogs.append(changelog)
    return selected_raw, selected_changelogs


def _filter_changelogs_by_field_ids(
    raw_changelogs: list[Mapping[str, Any]],
    changelogs: list[JiraChangelog],
    *,
    field_ids: list[str] | None,
) -> tuple[list[Mapping[str, Any]], list[JiraChangelog]]:
    """Prune changelog items by raw ``fieldId`` without changing source mappings."""
    if field_ids is None:
        return raw_changelogs, changelogs

    selected_field_ids = set(field_ids)
    selected_raw: list[Mapping[str, Any]] = []
    selected_changelogs: list[JiraChangelog] = []
    for raw_changelog, changelog in zip(raw_changelogs, changelogs, strict=True):
        raw_items = raw_changelog.get("items")
        if not isinstance(raw_items, list) or len(raw_items) != len(changelog.items):
            raise JiraHelperOperationError("Jira returned malformed changelog data.")

        matching_raw_items: list[Mapping[str, Any]] = []
        matching_items = []
        for raw_item, item in zip(raw_items, changelog.items, strict=True):
            if (
                isinstance(raw_item, Mapping)
                and raw_item.get("fieldId") in selected_field_ids
            ):
                matching_raw_items.append(cast(Mapping[str, Any], raw_item))
                matching_items.append(item)

        if matching_raw_items:
            filtered_raw_changelog = dict(raw_changelog)
            filtered_raw_changelog["items"] = matching_raw_items
            selected_raw.append(filtered_raw_changelog)
            selected_changelogs.append(
                changelog.model_copy(update={"items": matching_items})
            )
    return selected_raw, selected_changelogs


def _validate_result_pagination(
    result_start_at: int,
    result_max_results: int | None,
) -> tuple[int, int | None]:
    if (
        not isinstance(result_start_at, int)
        or isinstance(result_start_at, bool)
        or result_start_at < 0
    ):
        raise JiraHelperValidationError(
            "result_start_at must be a non-negative integer."
        )
    if result_max_results is None:
        if result_start_at != 0:
            raise JiraHelperValidationError(
                "result_start_at requires result_max_results."
            )
        return result_start_at, None
    if (
        not isinstance(result_max_results, int)
        or isinstance(result_max_results, bool)
        or result_max_results < 1
    ):
        raise JiraHelperValidationError("result_max_results must be at least 1.")
    return result_start_at, result_max_results


def _page_result(
    raw_changelogs: list[Mapping[str, Any]],
    changelogs: list[JiraChangelog],
    *,
    start_at: int,
    max_results: int,
) -> tuple[list[Mapping[str, Any]], list[JiraChangelog], dict[str, int | bool | None]]:
    total = len(raw_changelogs)
    page_raw = raw_changelogs[start_at : start_at + max_results]
    page_changelogs = changelogs[start_at : start_at + max_results]
    next_start_at = start_at + len(page_raw)
    if next_start_at >= total:
        next_start_at = None

    return (
        page_raw,
        page_changelogs,
        {
            "start_at": start_at,
            "max_results": max_results,
            "total": total,
            "is_last": next_start_at is None,
            "next_start_at": next_start_at,
        },
    )


def _result(
    issue_key: str,
    raw_changelogs: list[Mapping[str, Any]],
    changelogs: list[JiraChangelog],
    *,
    result_page: dict[str, int | bool | None] | None = None,
) -> HelperResult:
    data: dict[str, Any] = {"issue_key": issue_key, "changelogs": raw_changelogs}
    if result_page is not None:
        data["result_page"] = result_page
    return HelperResult.with_data(format_changelog_list(issue_key, changelogs), data)


__all__ = ["ChangelogHelpers"]
