from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import jira2py.helpers.comments as comments_module
from jira2py import JiraAPI
from jira2py.helpers.comments import CommentHelpers


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        comments=Mock(),
    )


def test_list_comments_formats_paging_and_next_page_hint() -> None:
    api = _make_api()
    api.comments.get_comments.return_value = {
        "startAt": 1,
        "total": 3,
        "comments": [
            {
                "author": {"displayName": "Alice"},
                "created": "2026-01-02T03:04:05.000+0000",
                "updated": "2026-01-03T03:04:05.000+0000",
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Comment body"}],
                        }
                    ],
                },
            }
        ],
    }

    result = CommentHelpers(cast(JiraAPI, api)).list(
        "PROJ-1",
        start_at=1,
        max_results=150,
        order_by="-updated",
    )

    api.comments.get_comments.assert_called_once_with(
        issue_id="PROJ-1",
        start_at=1,
        max_results=100,
        order_by="-updated",
    )
    assert result.data == api.comments.get_comments.return_value
    assert "Comments on PROJ-1: showing 2–2 of 3" in result.text
    assert "### Alice — 2026-01-02 (edited 2026-01-03)" in result.text
    assert "Comment body" in result.text
    assert "Use start_at=2 to fetch the next page" in result.text


def test_add_comment_converts_markdown_and_returns_browse_url(monkeypatch) -> None:
    api = _make_api()
    api.comments.add_comment.return_value = {"id": "10000"}
    monkeypatch.setattr(
        comments_module,
        "markdown_to_adf",
        lambda text: {"type": "doc", "markdown": text},
    )

    result = CommentHelpers(cast(JiraAPI, api)).add("PROJ-1", "Hello **world**")

    api.comments.add_comment.assert_called_once_with(
        issue_id="PROJ-1",
        body={"type": "doc", "markdown": "Hello **world**"},
    )
    assert result.data == {"id": "10000"}
    assert result.text == (
        "Added comment to PROJ-1\nURL: https://example.atlassian.net/browse/PROJ-1"
    )
