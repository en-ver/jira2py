"""Shared pytest fixtures for jira2py tests."""

from unittest.mock import Mock

import httpx
import pytest

from jira2py.client import JiraCredentials


@pytest.fixture(scope="session")
def base_url():
    """Shared base URL for all tests."""
    return "https://test.atlassian.net"


@pytest.fixture(scope="session")
def test_credentials(base_url):
    """Test credentials for JIRA client."""
    return JiraCredentials.create(
        url=base_url,
        username="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def mock_http_response():
    """Create mock httpx.Response for testing."""
    response = Mock(spec=httpx.Response)
    response.status_code = 404
    response.json.return_value = {
        "errorMessages": ["Issue does not exist"],
        "errors": {},
    }
    return response


@pytest.fixture
def make_client(test_credentials):
    """Factory fixture that creates a JiraClientSync with a mock handler.

    Cleans up injected persistent clients after each test to prevent state leakage.
    """
    from jira2py.client import JiraClientSync

    created_keys: list[str] = []

    def _factory(handler):
        client = JiraClientSync(test_credentials)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        created_keys.append(client._client_key)
        return client

    yield _factory

    for key in created_keys:
        JiraClientSync._class_persistent_clients.pop(key, None)


# Projects API fixtures


@pytest.fixture(scope="session")
def sample_projects_response():
    """Sample JIRA projects search response for testing."""
    return {
        "startAt": 0,
        "maxResults": 50,
        "total": 2,
        "isLast": True,
        "values": [
            {
                "id": "10000",
                "key": "PROJ",
                "name": "Project One",
                "description": "First test project",
                "lead": {"accountId": "user123", "displayName": "John Doe"},
            },
            {
                "id": "10001",
                "key": "TEST",
                "name": "Project Two",
                "description": "Second test project",
                "lead": {"accountId": "user456", "displayName": "Jane Smith"},
            },
        ],
    }


@pytest.fixture
def mock_transport_projects_success(sample_projects_response):
    """Mock HTTP transport that returns successful projects response."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "/project/search" in request.url.path:
            return httpx.Response(200, json=sample_projects_response)
        return httpx.Response(404, json={"message": "Not found"})

    return httpx.MockTransport(handler)


@pytest.fixture
def projects_client(test_credentials, mock_transport_projects_success):
    """Create a Projects API client with mocked transport."""
    from jira2py.api.projects import Projects
    from jira2py.client import JiraClientSync

    client = JiraClientSync(test_credentials)
    client._class_persistent_clients[client._client_key] = httpx.Client(
        transport=mock_transport_projects_success,
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    yield Projects(client)

    JiraClientSync._class_persistent_clients.pop(client._client_key, None)
