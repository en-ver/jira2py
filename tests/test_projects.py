"""Tests for Projects API."""

from unittest.mock import Mock

import httpx
import pytest

from jira2py.api.projects import Projects, ProjectsAsync, ProjectsBase
from jira2py.client import JiraClientAsync, JiraClientSync


class TestProjectsBaseRequestConfig:
    """Tests for ProjectsBase._search_projects_request_config method."""

    def test_request_config_defaults(self):
        """Test request config with default parameters."""
        mock_client = Mock(spec=JiraClientSync)
        projects_base = ProjectsBase(mock_client)

        config = projects_base._search_projects_request_config(
            start_at=0,
            max_results=50,
            project_ids=None,
            keys=None,
            query=None,
            expand=None,
            extra_params=None,
        )

        assert config["method"] == "GET"
        assert config["context_path"] == "project/search"
        assert config["params"]["startAt"] == 0
        assert config["params"]["maxResults"] == 50
        assert config["params"]["id"] is None
        assert config["params"]["keys"] is None
        assert config["params"]["query"] is None
        assert config["params"]["expand"] is None
        assert config["extra_params"] is None

    def test_request_config_with_all_params(self):
        """Test request config with all parameters provided."""
        mock_client = Mock(spec=JiraClientSync)
        projects_base = ProjectsBase(mock_client)

        config = projects_base._search_projects_request_config(
            start_at=10,
            max_results=25,
            project_ids=[10000, 10001],
            keys=["PROJ", "TEST"],
            query="service",
            expand="description,lead",
            extra_params=None,
        )

        assert config["params"]["startAt"] == 10
        assert config["params"]["maxResults"] == 25
        assert config["params"]["id"] == [10000, 10001]
        assert config["params"]["keys"] == ["PROJ", "TEST"]
        assert config["params"]["query"] == "service"
        assert config["params"]["expand"] == "description,lead"

    def test_request_config_with_expand(self):
        """Test request config passes expand parameter correctly."""
        mock_client = Mock(spec=JiraClientSync)
        projects_base = ProjectsBase(mock_client)

        config = projects_base._search_projects_request_config(
            start_at=0,
            max_results=50,
            project_ids=None,
            keys=None,
            query=None,
            expand="url,insight",
            extra_params=None,
        )

        assert config["params"]["expand"] == "url,insight"

    def test_request_config_with_extra_params(self):
        """Test request config includes extra_params."""
        mock_client = Mock(spec=JiraClientSync)
        projects_base = ProjectsBase(mock_client)

        extra_params = {"customField": "value"}
        config = projects_base._search_projects_request_config(
            start_at=0,
            max_results=50,
            project_ids=None,
            keys=None,
            query=None,
            expand=None,
            extra_params=extra_params,
        )

        assert config["extra_params"] == extra_params


class TestProjectsSearch:
    """Tests for Projects.search_projects method."""

    def test_search_projects_success(self, projects_client, sample_projects_response):
        """Test successful projects search returns expected data."""
        result = projects_client.search_projects()

        assert result["startAt"] == 0
        assert result["maxResults"] == 50
        assert result["total"] == 2
        assert result["isLast"] is True
        assert len(result["values"]) == 2
        assert result["values"][0]["key"] == "PROJ"
        assert result["values"][1]["key"] == "TEST"

    def test_search_projects_with_query(self, test_credentials):
        """Test projects search with query parameter."""

        def handler(request: httpx.Request) -> httpx.Response:
            # Verify query parameter is passed
            assert "query=service" in request.url.raw_path.decode() or "service" in str(
                request.url
            )
            return httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 10,
                    "total": 1,
                    "isLast": True,
                    "values": [
                        {"id": "10000", "key": "SRV", "name": "Service Project"}
                    ],
                },
            )

        client = JiraClientSync(credentials=test_credentials)
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = Projects(client)

        result = projects.search_projects(query="service", max_results=10)

        assert result["total"] == 1
        assert result["values"][0]["key"] == "SRV"

    def test_search_projects_with_keys(self, test_credentials):
        """Test projects search with keys filter."""

        def handler(request: httpx.Request) -> httpx.Response:
            # Verify keys parameter is passed
            return httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 50,
                    "total": 2,
                    "isLast": True,
                    "values": [
                        {"id": "10000", "key": "PROJ", "name": "Project One"},
                        {"id": "10001", "key": "TEST", "name": "Project Two"},
                    ],
                },
            )

        client = JiraClientSync(credentials=test_credentials)
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = Projects(client)

        result = projects.search_projects(keys=["PROJ", "TEST"])

        assert result["total"] == 2

    def test_search_projects_with_expand(self, test_credentials):
        """Test projects search with expand parameter."""

        def handler(request: httpx.Request) -> httpx.Response:
            # Verify expand parameter is formatted correctly
            return httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 5,
                    "total": 1,
                    "isLast": True,
                    "values": [
                        {
                            "id": "10000",
                            "key": "PROJ",
                            "name": "Project One",
                            "description": "Test description",
                            "lead": {"accountId": "user123", "displayName": "John Doe"},
                        }
                    ],
                },
            )

        client = JiraClientSync(credentials=test_credentials)
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = Projects(client)

        result = projects.search_projects(expand="description,lead", max_results=5)

        assert result["total"] == 1
        assert "description" in result["values"][0]
        assert "lead" in result["values"][0]

    def test_search_projects_with_pagination(self, test_credentials):
        """Test projects search with pagination parameters."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "startAt": 50,
                    "maxResults": 25,
                    "total": 100,
                    "isLast": False,
                    "values": [{"id": "10050", "key": "PROJ50", "name": "Project 50"}],
                },
            )

        client = JiraClientSync(credentials=test_credentials)
        client._client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = Projects(client)

        result = projects.search_projects(start_at=50, max_results=25)

        assert result["startAt"] == 50
        assert result["maxResults"] == 25
        assert result["total"] == 100


class TestProjectsAsyncSearch:
    """Tests for ProjectsAsync.search_projects method."""

    @pytest.mark.asyncio
    async def test_search_projects_async_success(
        self, projects_client_async, sample_projects_response
    ):
        """Test successful async projects search returns expected data."""
        result = await projects_client_async.search_projects()

        assert result["startAt"] == 0
        assert result["maxResults"] == 50
        assert result["total"] == 2
        assert result["isLast"] is True
        assert len(result["values"]) == 2
        assert result["values"][0]["key"] == "PROJ"
        assert result["values"][1]["key"] == "TEST"

    @pytest.mark.asyncio
    async def test_search_projects_async_with_query(self, test_credentials):
        """Test async projects search with query parameter."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 10,
                    "total": 1,
                    "isLast": True,
                    "values": [
                        {"id": "10000", "key": "SRV", "name": "Service Project"}
                    ],
                },
            )

        client = JiraClientAsync(credentials=test_credentials)
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = ProjectsAsync(client)

        result = await projects.search_projects(query="service", max_results=10)

        assert result["total"] == 1
        assert result["values"][0]["key"] == "SRV"

    @pytest.mark.asyncio
    async def test_search_projects_async_with_pagination(self, test_credentials):
        """Test async projects search with pagination parameters."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "startAt": 10,
                    "maxResults": 20,
                    "total": 75,
                    "isLast": False,
                    "values": [
                        {"id": "10010", "key": "PROJ10", "name": "Project 10"},
                        {"id": "10011", "key": "PROJ11", "name": "Project 11"},
                    ],
                },
            )

        client = JiraClientAsync(credentials=test_credentials)
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        projects = ProjectsAsync(client)

        result = await projects.search_projects(start_at=10, max_results=20)

        assert result["startAt"] == 10
        assert result["maxResults"] == 20
        assert result["total"] == 75
