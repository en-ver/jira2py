"""Tests for Issue Comments API."""

import httpx

from jira2py.api.api_base import _DEFAULT_PAGE_SIZE
from jira2py.api.issue_comments import IssueComments

SAMPLE_COMMENTS = {
    "startAt": 0,
    "maxResults": _DEFAULT_PAGE_SIZE,
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

    def test_get_comments_order_by(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["orderBy"] == "-created"
            return httpx.Response(200, json=SAMPLE_COMMENTS)

        api = IssueComments(make_client(handler))
        result = api.get_comments("TEST-1", order_by="-created")

        assert result["total"] == 1

    def test_get_comments_uses_shared_default_page_size(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["maxResults"] == str(_DEFAULT_PAGE_SIZE)
            return httpx.Response(200, json=SAMPLE_COMMENTS)

        api = IssueComments(make_client(handler))
        result = api.get_comments("TEST-1")

        assert result["maxResults"] == _DEFAULT_PAGE_SIZE

    def test_add_comment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=SAMPLE_COMMENT)

        api = IssueComments(make_client(handler))
        result = api.add_comment("TEST-1", body={"type": "doc", "content": []})

        assert result["id"] == "10001"

    def test_update_comment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/comment/10001"
            assert request.method == "PUT"
            return httpx.Response(200, json=SAMPLE_COMMENT)

        api = IssueComments(make_client(handler))
        result = api.update_comment(
            "TEST-1",
            "10001",
            body={"type": "doc", "content": []},
        )

        assert result["id"] == "10001"

    def test_delete_comment(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1/comment/10001"
            assert request.method == "DELETE"
            return httpx.Response(204)

        api = IssueComments(make_client(handler))

        assert api.delete_comment("TEST-1", "10001") is None
