"""Tests for Issue Search API."""

import httpx

from jira2py.api.issue_search import IssueSearch

SAMPLE_SEARCH = {
    "startAt": 0,
    "maxResults": 50,
    "total": 1,
    "issues": [
        {"id": "10000", "key": "TEST-1", "fields": {"summary": "Test issue"}},
    ],
}


class TestIssueSearch:
    """Tests for Issue Search API."""

    def test_enhanced_search(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_SEARCH)

        api = IssueSearch(make_client(handler))
        result = api.enhanced_search("project = TEST")

        assert result["total"] == 1
        assert result["issues"][0]["key"] == "TEST-1"

    def test_enhanced_search_with_fields(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_SEARCH)

        api = IssueSearch(make_client(handler))
        result = api.enhanced_search(
            "project = TEST", fields=["summary", "status"], max_results=10
        )

        assert result["total"] == 1
