"""Tests for Projects API."""

import httpx

from jira2py.api.projects import Projects

SAMPLE_PROJECTS = {
    "startAt": 0,
    "maxResults": 50,
    "total": 2,
    "isLast": True,
    "values": [
        {"id": "10000", "key": "PROJ", "name": "Project One"},
        {"id": "10001", "key": "TEST", "name": "Project Two"},
    ],
}


class TestProjectsSync:
    """Tests for sync Projects API."""

    def test_search_projects(self, projects_client, sample_projects_response):
        result = projects_client.search_projects()

        assert result["total"] == 2
        assert len(result["values"]) == 2
        assert result["values"][0]["key"] == "PROJ"

    def test_search_projects_with_query(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_PROJECTS)

        api = Projects(make_client(handler))
        result = api.search_projects(query="Project")

        assert result["total"] == 2

    def test_search_projects_with_keys(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_PROJECTS)

        api = Projects(make_client(handler))
        result = api.search_projects(keys=["PROJ"])

        assert result["total"] == 2

    def test_search_projects_empty(self, make_client):
        empty_response = {
            "startAt": 0,
            "maxResults": 50,
            "total": 0,
            "isLast": True,
            "values": [],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=empty_response)

        api = Projects(make_client(handler))
        result = api.search_projects()

        assert result["total"] == 0
        assert len(result["values"]) == 0
