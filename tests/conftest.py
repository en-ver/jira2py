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


@pytest.fixture(scope="session")
def sample_issue_response():
    """Sample JIRA issue response for testing."""
    return {
        "id": "10000",
        "key": "TEST-1",
        "fields": {
            "summary": "Test issue",
            "description": "Test description",
            "status": {"name": "To Do"},
            "issuetype": {"name": "Story"},
        },
    }


@pytest.fixture
def mock_transport_success(sample_issue_response):
    """Mock HTTP transport that returns successful responses."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "/issue/TEST-1" in request.url.path:
            return httpx.Response(200, json=sample_issue_response)
        return httpx.Response(404, json={"message": "Not found"})

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_transport_401():
    """Mock HTTP transport that returns 401 Unauthorized."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthorized"})

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_transport_404():
    """Mock HTTP transport that returns 404 Not Found."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not found"})

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_transport_429():
    """Mock HTTP transport that returns 429 Rate Limit."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "Rate limit exceeded"})

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_transport_500():
    """Mock HTTP transport that returns 500 Server Error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "Internal server error"})

    return httpx.MockTransport(handler)


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
def sync_client_with_transport(test_credentials, mock_transport_success):
    """Create a sync client with mocked transport."""
    # Create client with custom transport
    client = httpx.Client(
        transport=mock_transport_success,
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    return client


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
def mock_transport_projects_empty():
    """Mock HTTP transport that returns empty projects response."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "/project/search" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "startAt": 0,
                    "maxResults": 50,
                    "total": 0,
                    "isLast": True,
                    "values": [],
                },
            )
        return httpx.Response(404, json={"message": "Not found"})

    return httpx.MockTransport(handler)


@pytest.fixture
def projects_client(test_credentials, mock_transport_projects_success):
    """Create a Projects API client with mocked transport."""
    from jira2py.api.projects import Projects
    from jira2py.client import JiraClientSync

    client = JiraClientSync(credentials=test_credentials)
    # Inject the mock transport
    client._client = httpx.Client(
        transport=mock_transport_projects_success,
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    return Projects(client)


@pytest.fixture
def projects_client_async(test_credentials, mock_transport_projects_success):
    """Create a ProjectsAsync API client with mocked transport."""
    from jira2py.api.projects import ProjectsAsync
    from jira2py.client import JiraClientAsync

    client = JiraClientAsync(credentials=test_credentials)
    # Inject the mock transport
    client._client = httpx.AsyncClient(
        transport=mock_transport_projects_success,
        base_url=f"{test_credentials.url}/rest/api/3",
        auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
    )
    return ProjectsAsync(client)
