"""Tests for metadata API groups."""

import httpx

from jira2py import JiraAPI
from jira2py.api.metadata import Metadata

SAMPLE_STATUSES = [
    {
        "id": "1",
        "name": "To Do",
        "description": "Initial status",
        "statusCategory": {"id": 2, "key": "new", "name": "To Do"},
    },
    {
        "id": "3",
        "name": "Done",
        "statusCategory": {"id": 3, "key": "done", "name": "Done"},
    },
]

SAMPLE_PRIORITIES = [
    {
        "id": "1",
        "name": "Highest",
        "description": "Top urgency",
        "isDefault": False,
    },
    {
        "id": "5",
        "name": "Medium",
        "isDefault": True,
    },
]


class TestMetadata:
    """Tests for metadata API."""

    def test_get_statuses(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/status"
            return httpx.Response(200, json=SAMPLE_STATUSES)

        api = Metadata(make_client(handler))
        result = api.get_statuses()

        assert result == SAMPLE_STATUSES

    def test_get_priorities(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/priority"
            return httpx.Response(200, json=SAMPLE_PRIORITIES)

        api = Metadata(make_client(handler))
        result = api.get_priorities()

        assert result == SAMPLE_PRIORITIES


class TestJiraAPIMetadataFacade:
    """Tests for JiraAPI metadata facade."""

    def test_metadata_property_is_cached(self):
        jira = JiraAPI(
            url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test-token",
        )

        first = jira.metadata
        second = jira.metadata

        assert isinstance(first, Metadata)
        assert first is second
