"""Grouped changelog helper operations for jira2py."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from jira2py.api import JiraAPI

from ._text import format_changelog_list
from ._validation import parse_iso_datetime, require_non_empty_string
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
    ) -> HelperResult:
        """Retrieve every changelog page, optionally filtering by creation time."""
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
        return _result(issue_key, selected_raw, selected_changelogs)

    def list_by_ids(
        self,
        issue_key: str,
        changelog_ids: Sequence[int],
    ) -> HelperResult:
        """Retrieve the changelog histories identified by known Jira IDs."""
        issue_key = require_non_empty_string(issue_key, field_name="issue_key")
        ids = _validate_changelog_ids(changelog_ids)

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
        return _result(issue_key, raw_changelogs, changelogs)


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


def _result(
    issue_key: str,
    raw_changelogs: list[Mapping[str, Any]],
    changelogs: list[JiraChangelog],
) -> HelperResult:
    data = {"issue_key": issue_key, "changelogs": raw_changelogs}
    return HelperResult.with_data(format_changelog_list(issue_key, changelogs), data)


__all__ = ["ChangelogHelpers"]
