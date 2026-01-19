"""Tests for JIRA client layer."""

import httpx
import pytest

from jira2py.client import JiraCredentials, JiraClientSync
from jira2py.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)


class TestJiraCredentials:
    """Tests for JiraCredentials dataclass."""

    def test_credentials_initialization(self, base_url):
        """Test that credentials can be initialized with explicit values."""
        credentials = JiraCredentials(
            url=base_url,
            username="test@example.com",
            api_token="test-token",
        )
        assert credentials.url == base_url
        assert credentials.username == "test@example.com"
        assert credentials.api_token == "test-token"
        # Token should be hidden from repr
        assert "test-token" not in repr(credentials)

    def test_credentials_url_validation(self):
        """Test that credentials validate URL format."""
        with pytest.raises(ValueError, match="must start with"):
            JiraCredentials(
                url="invalid-url", username="test@example.com", api_token="token"
            )

    def test_credentials_missing_url(self):
        """Test that credentials require URL."""
        with pytest.raises(ValueError, match="URL is required"):
            JiraCredentials(url=None, username="test@example.com", api_token="token")

    def test_credentials_missing_username(self):
        """Test that credentials require username."""
        with pytest.raises(ValueError, match="username is required"):
            JiraCredentials(url="https://test.com", username=None, api_token="token")

    def test_credentials_missing_token(self):
        """Test that credentials require API token."""
        with pytest.raises(ValueError, match="token is required"):
            JiraCredentials(
                url="https://test.com", username="test@example.com", api_token=None
            )

    def test_credentials_url_trailing_slash_removal(self):
        """Test that credentials remove trailing slashes from URL."""
        credentials = JiraCredentials(
            url="https://test.com/",
            username="test@example.com",
            api_token="token",
        )
        assert credentials.url == "https://test.com"
        assert not credentials.url.endswith("/")

    def test_credentials_frozen(self):
        """Test that credentials dataclass is frozen."""
        credentials = JiraCredentials(
            url="https://test.com",
            username="test@example.com",
            api_token="token",
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            credentials.url = "https://other.com"  # type: ignore[misc]


class TestJiraClientSync:
    """Tests for synchronous JIRA client."""

    def test_client_initialization_with_credentials(self, test_credentials):
        """Test that client can be initialized with credentials object."""
        client = JiraClientSync(credentials=test_credentials)
        assert client.credentials == test_credentials

    def test_client_initialization_with_parameters(self, base_url):
        """Test that client can be initialized with individual parameters."""
        client = JiraClientSync(
            url=base_url,
            username="test@example.com",
            api_token="test-token",
        )
        assert client.credentials.url == base_url
        assert client.credentials.username == "test@example.com"
        assert client.credentials.api_token == "test-token"

    def test_client_get_client_type(self, test_credentials):
        """Test that client returns correct client type."""
        client = JiraClientSync(credentials=test_credentials)
        assert client._get_client_type() == httpx.Client
        assert client._get_async_mode() is False

    def test_client_context_manager(self, test_credentials):
        """Test that client works as context manager."""
        client = JiraClientSync(credentials=test_credentials)
        with client:
            assert client._client is not None
        assert client._client is None

    def test_client_close(self, test_credentials):
        """Test that client can be closed."""
        client = JiraClientSync(credentials=test_credentials)
        # Create a temporary client
        client._client = client._get_client()
        assert client._client is not None

        client.close()
        assert client._client is None


class TestClientErrorHandling:
    """Tests for client error handling."""

    def test_handle_error_with_timeout(self, test_credentials):
        """Test that timeout errors raise JiraConnectionError."""
        client = JiraClientSync(credentials=test_credentials)
        timeout_error = httpx.TimeoutException("Request timed out")

        with pytest.raises(JiraConnectionError) as exc_info:
            client._handle_error(timeout_error)

        assert "timed out" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is timeout_error

    def test_handle_error_with_network_error(self, test_credentials):
        """Test that network errors raise JiraConnectionError."""
        client = JiraClientSync(credentials=test_credentials)
        network_error = httpx.NetworkError("Connection failed")

        with pytest.raises(JiraConnectionError) as exc_info:
            client._handle_error(network_error)

        assert "network error" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is network_error

    def test_handle_error_with_unknown_error(self, test_credentials):
        """Test that unknown errors raise JiraError."""
        client = JiraClientSync(credentials=test_credentials)
        unknown_error = RuntimeError("Unknown error")

        with pytest.raises(JiraError) as exc_info:
            client._handle_error(unknown_error)

        assert "unexpected error" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is unknown_error

    def test_extract_error_messages_from_error_messages_field(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from errorMessages field."""
        mock_http_response.json.return_value = {"errorMessages": ["Error 1", "Error 2"]}

        client = JiraClientSync(credentials=test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == ["Error 1", "Error 2"]

    def test_extract_error_messages_from_errors_field(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from errors field."""
        mock_http_response.json.return_value = {
            "errors": {"field1": "Error 1", "field2": "Error 2"}
        }

        client = JiraClientSync(credentials=test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert set(messages) == {"Error 1", "Error 2"}

    def test_extract_error_messages_from_message_field(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error message from message field."""
        mock_http_response.json.return_value = {"message": "Single error message"}

        client = JiraClientSync(credentials=test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == ["Single error message"]

    def test_extract_error_messages_empty_response(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from empty response."""
        mock_http_response.json.return_value = {}

        client = JiraClientSync(credentials=test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == []

    def test_extract_error_messages_invalid_json(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from invalid JSON."""
        mock_http_response.json.side_effect = ValueError("Invalid JSON")

        client = JiraClientSync(credentials=test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == []


@pytest.mark.parametrize(
    "status_code,exception_class,error_message",
    [
        (401, JiraAuthenticationError, "Authentication failed"),
        (403, JiraAuthenticationError, "Access forbidden"),
        (404, JiraNotFoundError, "Resource not found"),
        (429, JiraRateLimitError, "Rate limit exceeded"),
        (400, JiraValidationError, "Request validation failed"),
        (500, JiraAPIError, "Server error"),
        (502, JiraAPIError, "Server error"),
        (422, JiraAPIError, "Client error"),
    ],
)
class TestHTTPStatusMapping:
    """Tests for HTTP status code to exception mapping."""

    def test_http_status_mapping(
        self,
        test_credentials,
        status_code,
        exception_class,
        error_message,
    ):
        """Test that HTTP status codes map to correct exceptions."""
        client = JiraClientSync(credentials=test_credentials)

        # Create a mock HTTPStatusError
        mock_request = httpx.Request(
            "GET", "https://test.atlassian.net/rest/api/3/issue/TEST-1"
        )
        mock_response = httpx.Response(
            status_code,
            json={"message": "Error"},
            request=mock_request,
        )
        http_error = httpx.HTTPStatusError(
            "HTTP error", request=mock_request, response=mock_response
        )

        # Check that the correct exception is raised
        with pytest.raises(exception_class) as exc_info:
            client._handle_error(http_error)

        assert error_message.lower() in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is http_error
