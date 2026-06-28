"""Tests for filters API."""

import httpx

from jira2py import JiraAPI
from jira2py.api.filters import Filters

SAMPLE_FILTERS = {
    "isLast": False,
    "total": 2,
    "values": [
        {
            "id": "10100",
            "name": "My open issues",
            "jql": "assignee = currentUser() AND resolution = Unresolved",
            "owner": {"displayName": "Alice Example", "accountId": "acct-1"},
        }
    ],
}

SAMPLE_FILTER = {
    "id": "10100",
    "name": "My open issues",
    "jql": "assignee = currentUser() AND resolution = Unresolved",
}


class TestFilters:
    """Tests for filters API."""

    def test_search_filters(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/filter/search"
            assert request.url.params["filterName"] == "open"
            assert request.url.params["expand"] == "owner,jql"
            assert request.url.params["orderBy"] == "name"
            return httpx.Response(200, json=SAMPLE_FILTERS)

        api = Filters(make_client(handler))
        result = api.search_filters(
            filter_name="open",
            expand="owner,jql",
            order_by="name",
        )

        assert result["values"][0]["id"] == "10100"

    def test_get_filter(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/filter/10100"
            assert request.url.params["expand"] == "jql"
            return httpx.Response(200, json=SAMPLE_FILTER)

        api = Filters(make_client(handler))
        result = api.get_filter("10100", expand="jql")

        assert result["jql"] == SAMPLE_FILTER["jql"]


class TestJiraAPIFiltersFacade:
    """Tests for JiraAPI filters facade."""

    def test_filters_property_is_cached(self):
        jira = JiraAPI(
            url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test-token",
        )

        first = jira.filters
        second = jira.filters

        assert isinstance(first, Filters)
        assert first is second
