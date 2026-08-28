from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, call

import pytest

from jira2py import JiraAPI
from jira2py.helpers.changelogs import ChangelogHelpers
from jira2py.helpers.errors import JiraHelperOperationError, JiraHelperValidationError


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(issues=Mock())


def _page(
    values: list[dict[str, Any]],
    *,
    start_at: int,
    is_last: bool,
) -> dict[str, Any]:
    return {"values": values, "startAt": start_at, "isLast": is_last}


def test_list_fetches_every_page_in_returned_order_and_preserves_raw_data() -> None:
    api = _make_api()
    first = {
        "id": "100",
        "created": "2026-01-02T00:00:00Z",
        "author": {"displayName": "Alice"},
        "items": [
            {
                "field": "status",
                "fromString": "Open",
                "toString": "In Progress",
            }
        ],
        "unknownHistoryField": {"retained": True},
    }
    second = {
        "id": "101",
        "created": "2026-01-03T00:00:00Z",
        "author": {"displayName": "Bob"},
        "items": [{"fieldId": "customfield_10001", "from": "A", "to": "B"}],
    }
    api.issues.get_changelogs.side_effect = [
        _page([first], start_at=4, is_last=False),
        _page([second], start_at=5, is_last=True),
    ]

    result = ChangelogHelpers(cast(JiraAPI, api)).list("PROJ-1")

    assert api.issues.get_changelogs.call_args_list == [
        call(issue_id="PROJ-1", start_at=0),
        call(issue_id="PROJ-1", start_at=5),
    ]
    assert result.data == {"issue_key": "PROJ-1", "changelogs": [first, second]}
    assert "Changelogs on PROJ-1: 2 returned" in result.text
    assert "Alice — id 100" in result.text
    assert "status: Open → In Progress" in result.text
    assert "customfield_10001: A → B" in result.text


def test_list_filters_complete_history_with_utc_half_open_bounds() -> None:
    api = _make_api()
    values = [
        {"id": "before", "created": "2026-01-01T23:59:59Z", "items": []},
        {"id": "lower", "created": "2026-01-02T02:00:00+0200", "items": []},
        {"id": "inside", "created": "2026-01-02T00:30:00", "items": []},
        {"id": "upper", "created": "2026-01-02T01:00:00+0000", "items": []},
    ]
    api.issues.get_changelogs.return_value = _page(values, start_at=0, is_last=True)

    result = ChangelogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        created_at_or_after="2026-01-02T00:00:00Z",
        created_before="2026-01-02T01:00:00Z",
    )

    assert result.data == {
        "issue_key": "PROJ-1",
        "changelogs": [values[1], values[2]],
    }


def test_list_retains_invalid_created_values_unfiltered_and_excludes_them_filtered() -> (
    None
):
    api = _make_api()
    values = [
        {"id": "bad", "created": "not-a-date", "items": []},
        {"id": "missing", "items": []},
    ]
    api.issues.get_changelogs.return_value = _page(values, start_at=0, is_last=True)
    helper = ChangelogHelpers(cast(JiraAPI, api))

    assert helper.list("PROJ-1").data == {
        "issue_key": "PROJ-1",
        "changelogs": values,
    }
    assert helper.list("PROJ-1", created_at_or_after="2026-01-01").data == {
        "issue_key": "PROJ-1",
        "changelogs": [],
    }


def test_list_validates_bounds_before_requesting_jira() -> None:
    api = _make_api()
    helper = ChangelogHelpers(cast(JiraAPI, api))

    with pytest.raises(JiraHelperValidationError, match="created_at_or_after"):
        helper.list("PROJ-1", created_at_or_after="not-a-date")
    with pytest.raises(JiraHelperValidationError, match="created_before"):
        helper.list(
            "PROJ-1",
            created_at_or_after="2026-01-02",
            created_before="2026-01-01",
        )
    with pytest.raises(JiraHelperValidationError, match="created_before"):
        helper.list("PROJ-1", created_before=cast(Any, 42))
    with pytest.raises(JiraHelperValidationError, match="field_ids"):
        helper.list("PROJ-1", field_ids=cast(Any, "summary"))
    with pytest.raises(JiraHelperValidationError, match="result_start_at"):
        helper.list("PROJ-1", result_start_at=1)
    with pytest.raises(JiraHelperValidationError, match="result_max_results"):
        helper.list("PROJ-1", result_max_results=0)

    api.issues.get_changelogs.assert_not_called()


def test_list_completes_equal_bounds_and_rejects_broken_pagination() -> None:
    api = _make_api()
    api.issues.get_changelogs.side_effect = [
        _page(
            [{"id": "100", "created": "2026-01-02", "items": []}],
            start_at=0,
            is_last=False,
        ),
        _page(
            [{"id": "101", "created": "2026-01-02", "items": []}],
            start_at=1,
            is_last=True,
        ),
    ]

    result = ChangelogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        created_at_or_after="2026-01-02",
        created_before="2026-01-02",
    )

    assert result.data == {"issue_key": "PROJ-1", "changelogs": []}
    assert api.issues.get_changelogs.call_count == 2

    api = _make_api()
    api.issues.get_changelogs.return_value = _page([], start_at=0, is_last=False)
    with pytest.raises(JiraHelperOperationError, match="did not advance"):
        ChangelogHelpers(cast(JiraAPI, api)).list("PROJ-1")


def test_list_translates_request_and_response_shape_failures() -> None:
    api = _make_api()
    api.issues.get_changelogs.side_effect = [
        _page([{"id": "100", "items": []}], start_at=0, is_last=False),
        RuntimeError("boom"),
    ]

    with pytest.raises(JiraHelperOperationError, match="Failed to fetch changelogs"):
        ChangelogHelpers(cast(JiraAPI, api)).list("PROJ-1")

    api = _make_api()
    api.issues.get_changelogs.return_value = {
        "values": [],
        "startAt": 0,
        "isLast": "true",
    }
    with pytest.raises(JiraHelperOperationError, match="malformed changelog page"):
        ChangelogHelpers(cast(JiraAPI, api)).list("PROJ-1")


def test_list_filters_raw_items_by_exact_field_id_without_mutating_source() -> None:
    api = _make_api()
    first = {
        "id": "100",
        "created": "2026-01-02T00:00:00Z",
        "items": [
            {
                "field": "Summary",
                "fieldId": "summary",
                "fromString": "Old",
                "toString": "New",
                "unknownItemField": None,
            },
            {"field": "Status", "fieldId": "status"},
            {"field": "Summary"},
            {"field": "Priority", "fieldId": None},
        ],
        "unknownHistoryField": {"retained": True},
    }
    second = {
        "id": "101",
        "created": "2026-01-03T00:00:00Z",
        "items": [{"fieldId": "customfield_10001", "unknown": None}],
    }
    unmatched = {
        "id": "102",
        "created": "2026-01-04T00:00:00Z",
        "items": [{"fieldId": "status"}],
    }
    api.issues.get_changelogs.return_value = _page(
        [first, second, unmatched],
        start_at=0,
        is_last=True,
    )

    result = ChangelogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        field_ids=["summary", "customfield_10001"],
    )

    data = result.data
    assert isinstance(data, dict)
    filtered = data["changelogs"]
    assert [changelog["id"] for changelog in filtered] == ["100", "101"]
    assert filtered[0] is not first
    assert list(filtered[0]) == list(first)
    assert filtered[0]["unknownHistoryField"] is first["unknownHistoryField"]
    assert filtered[0]["items"] == [first["items"][0]]
    assert filtered[0]["items"][0] is first["items"][0]
    assert filtered[1]["items"] == [second["items"][0]]
    assert first["items"] == [
        {
            "field": "Summary",
            "fieldId": "summary",
            "fromString": "Old",
            "toString": "New",
            "unknownItemField": None,
        },
        {"field": "Status", "fieldId": "status"},
        {"field": "Summary"},
        {"field": "Priority", "fieldId": None},
    ]
    assert "Summary: Old → New" in result.text
    assert "Status" not in result.text

    no_matches = ChangelogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        field_ids=["Summary"],
    )
    assert no_matches.data == {"issue_key": "PROJ-1", "changelogs": []}


def test_list_fetches_complete_history_before_paging_filtered_events() -> None:
    api = _make_api()
    before = {
        "id": "before",
        "created": "2026-01-01",
        "items": [{"fieldId": "summary"}],
    }
    first = {"id": "first", "created": "2026-01-02", "items": [{"fieldId": "summary"}]}
    second = {
        "id": "second",
        "created": "2026-01-03",
        "items": [{"fieldId": "summary"}],
    }
    api.issues.get_changelogs.side_effect = [
        _page([before, first], start_at=0, is_last=False),
        _page([second], start_at=2, is_last=True),
    ]

    result = ChangelogHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        created_at_or_after="2026-01-02",
        field_ids=["summary"],
        result_start_at=1,
        result_max_results=1,
    )

    assert api.issues.get_changelogs.call_args_list == [
        call(issue_id="PROJ-1", start_at=0),
        call(issue_id="PROJ-1", start_at=2),
    ]
    assert result.data == {
        "issue_key": "PROJ-1",
        "changelogs": [second],
        "result_page": {
            "start_at": 1,
            "max_results": 1,
            "total": 2,
            "is_last": True,
            "next_start_at": None,
        },
    }


def test_list_by_ids_uses_one_request_and_extracts_server_ordered_histories() -> None:
    api = _make_api()
    server_order = [
        {
            "id": "102",
            "created": "2026-01-02T00:00:00Z",
            "items": [],
            "unknownHistoryField": {"retained": True},
        },
        {"id": "100", "created": "2026-01-01T00:00:00Z", "items": []},
    ]
    api.issues.get_changelogs_by_ids.return_value = {
        "histories": server_order,
        "startAt": 0,
        "maxResults": 2,
        "total": 2,
    }

    result = ChangelogHelpers(cast(JiraAPI, api)).list_by_ids(
        "PROJ-1",
        [100, 102, 100],
    )

    api.issues.get_changelogs_by_ids.assert_called_once_with(
        issue_id="PROJ-1",
        changelog_ids=[100, 102, 100],
    )
    assert result.data == {"issue_key": "PROJ-1", "changelogs": server_order}


def test_list_by_ids_filters_items_without_result_pagination() -> None:
    api = _make_api()
    history = {
        "id": "102",
        "created": "2026-01-02T00:00:00Z",
        "items": [
            {"fieldId": "summary", "fromString": "Old", "toString": "New"},
            {"fieldId": "status"},
        ],
        "unknownHistoryField": None,
    }
    api.issues.get_changelogs_by_ids.return_value = {"histories": [history]}

    result = ChangelogHelpers(cast(JiraAPI, api)).list_by_ids(
        "PROJ-1",
        [102],
        field_ids=["summary"],
    )

    assert result.data == {
        "issue_key": "PROJ-1",
        "changelogs": [
            {
                "id": "102",
                "created": "2026-01-02T00:00:00Z",
                "items": [history["items"][0]],
                "unknownHistoryField": None,
            }
        ],
    }
    data = result.data
    assert isinstance(data, dict)
    assert "result_page" not in data
    assert history["items"] == [
        {"fieldId": "summary", "fromString": "Old", "toString": "New"},
        {"fieldId": "status"},
    ]


def test_list_by_ids_rejects_a_non_page_response() -> None:
    api = _make_api()
    api.issues.get_changelogs_by_ids.return_value = [
        {"id": "100", "created": "2026-01-01T00:00:00Z", "items": []}
    ]

    with pytest.raises(JiraHelperOperationError, match="malformed changelog data"):
        ChangelogHelpers(cast(JiraAPI, api)).list_by_ids("PROJ-1", [100])


@pytest.mark.parametrize("changelog_ids", [[], "100", [True], [100, "101"]])
def test_list_by_ids_validates_ids_before_requesting_jira(
    changelog_ids: object,
) -> None:
    api = _make_api()

    with pytest.raises(JiraHelperValidationError, match="changelog_ids"):
        ChangelogHelpers(cast(JiraAPI, api)).list_by_ids(
            "PROJ-1",
            cast(Any, changelog_ids),
        )

    api.issues.get_changelogs_by_ids.assert_not_called()


def test_list_by_ids_validates_field_ids_before_requesting_jira() -> None:
    api = _make_api()

    with pytest.raises(JiraHelperValidationError, match="field_ids"):
        ChangelogHelpers(cast(JiraAPI, api)).list_by_ids(
            "PROJ-1",
            [100],
            field_ids=cast(Any, ["summary,status"]),
        )

    api.issues.get_changelogs_by_ids.assert_not_called()
