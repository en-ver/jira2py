"""Tests for Issue Fields API."""

import httpx

from jira2py.api.issue_fields import IssueFields

SAMPLE_FIELDS = [
    {"id": "summary", "name": "Summary", "custom": False},
    {"id": "customfield_10001", "name": "Story Points", "custom": True},
]


class TestIssueFields:
    """Tests for Issue Fields API."""

    def test_get_fields(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_FIELDS)

        api = IssueFields(make_client(handler))
        result = api.get_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
        assert result[1]["custom"] is True
