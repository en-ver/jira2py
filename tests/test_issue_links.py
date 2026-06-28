"""Tests for Issue Links API."""

import httpx

from jira2py.api.issue_links import IssueLinks

SAMPLE_LINK_TYPES = {
    "issueLinkTypes": [
        {
            "id": "10000",
            "name": "Blocks",
            "inward": "is blocked by",
            "outward": "blocks",
        },
        {
            "id": "10001",
            "name": "Clones",
            "inward": "is cloned by",
            "outward": "clones",
        },
    ]
}

SAMPLE_ISSUE_LINKS = {
    "key": "TEST-1",
    "fields": {
        "issuelinks": [
            {
                "id": "10000",
                "type": {
                    "name": "Blocks",
                    "inward": "is blocked by",
                    "outward": "blocks",
                },
                "outwardIssue": {
                    "key": "TEST-2",
                    "fields": {
                        "summary": "Linked issue",
                        "status": {"name": "In Progress"},
                    },
                },
            }
        ]
    },
}


class TestIssueLinks:
    """Tests for Issue Links API."""

    def test_get_issue_links(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/issue/TEST-1"
            assert request.url.params["fields"] == "issuelinks"
            return httpx.Response(200, json=SAMPLE_ISSUE_LINKS)

        api = IssueLinks(make_client(handler))
        result = api.get_issue_links("TEST-1")

        assert len(result) == 1
        assert result[0]["id"] == "10000"

    def test_get_link_types(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_LINK_TYPES)

        api = IssueLinks(make_client(handler))
        result = api.get_link_types()

        assert len(result["issueLinkTypes"]) == 2
        assert result["issueLinkTypes"][0]["name"] == "Blocks"

    def test_create_link(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201)

        api = IssueLinks(make_client(handler))
        result = api.create_link("Blocks", "TEST-1", "TEST-2")

        assert result is None

    def test_delete_link(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(204)

        api = IssueLinks(make_client(handler))
        result = api.delete_link("10000")

        assert result is None
