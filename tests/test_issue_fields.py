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
            assert request.url.path == "/rest/api/3/field"
            assert not request.url.params
            return httpx.Response(200, json=SAMPLE_FIELDS)

        api = IssueFields(make_client(handler))
        result = api.get_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
        assert result[1]["custom"] is True

    def test_search_fields_returns_one_raw_page_with_named_parameters(
        self, make_client
    ):
        page = {
            "startAt": 2,
            "maxResults": 5,
            "total": 6,
            "isLast": False,
            "values": SAMPLE_FIELDS,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/field/search"
            assert request.url.params["startAt"] == "2"
            assert request.url.params["maxResults"] == "5"
            assert request.url.params["query"] == "points"
            assert request.url.params.get_list("id") == [
                "summary",
                "customfield_10001",
            ]
            assert request.url.params.get_list("type") == ["system", "custom"]
            assert request.url.params.get_list("projectIds") == ["10000"]
            assert request.url.params["orderBy"] == "name"
            assert request.url.params["expand"] == "key,stableId"
            return httpx.Response(200, json=page)

        api = IssueFields(make_client(handler))
        result = api.search_fields(
            start_at=2,
            max_results=5,
            query="points",
            field_ids=["summary", "customfield_10001"],
            field_types=["system", "custom"],
            project_ids=[10000],
            order_by="name",
            expand="key,stableId",
        )

        assert result == page

    def test_search_fields_extra_params_override_named_parameters(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["startAt"] == "9"
            assert request.url.params["query"] == "override"
            assert request.url.params["extra"] == "value"
            return httpx.Response(200, json={"values": [], "isLast": True})

        api = IssueFields(make_client(handler))
        api.search_fields(
            start_at=2,
            query="named",
            extra_params={"startAt": 9, "query": "override", "extra": "value"},
        )
