from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

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
                            "content": [
                                {"type": "text", "text": "Comment body for "},
                                {
                                    "type": "mention",
                                    "attrs": {
                                        "id": "557057:User:AbC",
                                        "text": "@Alice",
                                    },
                                },
                            ],
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
    assert "Comment body for @Alice" in result.text
    assert "Use start_at=2 to fetch the next page" in result.text


def test_add_comment_converts_jira_mention_and_returns_browse_url() -> None:
    api = _make_api()
    api.comments.add_comment.return_value = {"id": "10000"}

    result = CommentHelpers(cast(JiraAPI, api)).add(
        "PROJ-1", "[~accountId:557057:User:AbC]"
    )

    api.comments.add_comment.assert_called_once_with(
        issue_id="PROJ-1",
        body={
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "mention", "attrs": {"id": "557057:User:AbC"}}
                    ],
                }
            ],
        },
    )
    assert result.data == {"id": "10000"}
    assert result.text == (
        "Added comment to PROJ-1\nURL: https://example.atlassian.net/browse/PROJ-1"
    )


def test_update_comment_converts_jira_mention_and_uses_presentation_output() -> None:
    api = _make_api()
    api.comments.update_comment.return_value = {
        "id": "10000",
        "author": {"displayName": "Alice"},
        "created": "2026-01-02T03:04:05.000+0000",
        "updated": "2026-01-03T03:04:05.000+0000",
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Updated body for "},
                        {
                            "type": "mention",
                            "attrs": {
                                "id": "557057:User:AbC",
                                "text": "@Alice",
                            },
                        },
                    ],
                }
            ],
        },
    }

    result = CommentHelpers(cast(JiraAPI, api)).update(
        "PROJ-1",
        "10000",
        "Updated [~accountId:557057:User:AbC]",
    )

    api.comments.update_comment.assert_called_once_with(
        issue_id="PROJ-1",
        comment_id="10000",
        body={
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Updated "},
                        {"type": "mention", "attrs": {"id": "557057:User:AbC"}},
                    ],
                }
            ],
        },
    )
    assert result.data == api.comments.update_comment.return_value
    assert "Updated comment 10000 on PROJ-1" in result.text
    assert "### Alice — 2026-01-02 (edited 2026-01-03)" in result.text
    assert "Updated body for @Alice" in result.text


def test_delete_comment_returns_explicit_ids_without_confirmation() -> None:
    api = _make_api()

    result = CommentHelpers(cast(JiraAPI, api)).delete("PROJ-1", "10000")

    api.comments.delete_comment.assert_called_once_with(
        issue_id="PROJ-1",
        comment_id="10000",
    )
    assert result.data == {
        "status": "deleted",
        "issue_key": "PROJ-1",
        "comment_id": "10000",
    }
    assert result.text == (
        "Deleted comment 10000 from PROJ-1\n"
        "URL: https://example.atlassian.net/browse/PROJ-1"
    )
