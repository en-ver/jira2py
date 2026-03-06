"""Tests for Issue Comments API."""

import httpx

from jira2py.api.issue_comments import IssueComments

SAMPLE_COMMENTS = {
    "startAt": 0,
    "maxResults": 100,
    "total": 1,
    "comments": [
        {"id": "10000", "body": {"type": "doc", "content": []}},
    ],
}

SAMPLE_COMMENT = {
    "id": "10001",
    "body": {"type": "doc", "content": []},
    "author": {"displayName": "Test User"},
}


class TestIssueComments:
    """Tests for Issue Comments API."""

    def test_get_comments(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_COMMENTS)

        api = IssueComments(make_client(handler))
        result = api.get_comments("TEST-1")

        assert result["total"] == 1
        assert len(result["comments"]) == 1

    def test_add_comment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_COMMENT)

        api = IssueComments(make_client(handler))
        result = api.add_comment("TEST-1", body={"type": "doc", "content": []})

        assert result["id"] == "10001"
