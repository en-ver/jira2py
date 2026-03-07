"""Tests for JIRA client layer."""

import dataclasses
from unittest.mock import patch

import httpx
import pytest

from jira2py.client import JiraClientSync, JiraCredentials
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
        credentials = JiraCredentials.create(
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
            JiraCredentials.create(
                url="invalid-url", username="test@example.com", api_token="token"
            )

    def test_credentials_missing_url(self, monkeypatch):
        """Test that credentials require URL."""
        monkeypatch.delenv("JIRA_URL", raising=False)
        with pytest.raises(ValueError, match="URL is required"):
            JiraCredentials.create(
                url=None, username="test@example.com", api_token="token"
            )

    def test_credentials_missing_username(self, monkeypatch):
        """Test that credentials require username."""
        monkeypatch.delenv("JIRA_USER", raising=False)
        with pytest.raises(ValueError, match="username is required"):
            JiraCredentials.create(
                url="https://test.com", username=None, api_token="token"
            )

    def test_credentials_missing_token(self, monkeypatch):
        """Test that credentials require API token."""
        monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
        with pytest.raises(ValueError, match="token is required"):
            JiraCredentials.create(
                url="https://test.com", username="test@example.com", api_token=None
            )

    def test_credentials_url_trailing_slash_removal(self):
        """Test that credentials remove trailing slashes from URL."""
        credentials = JiraCredentials.create(
            url="https://test.com/",
            username="test@example.com",
            api_token="token",
        )
        assert credentials.url == "https://test.com"
        assert not credentials.url.endswith("/")

    def test_credentials_frozen(self):
        """Test that credentials dataclass is frozen."""
        credentials = JiraCredentials.create(
            url="https://test.com",
            username="test@example.com",
            api_token="token",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            credentials.url = "https://other.com"  # type: ignore[misc]


class TestJiraClientSync:
    """Tests for synchronous JIRA client."""

    def test_client_initialization(self, test_credentials):
        """Test that client can be initialized with credentials object."""
        client = JiraClientSync(test_credentials)
        assert client.credentials == test_credentials

    def test_persistent_client_reuse(self, test_credentials):
        """Test that persistent clients are reused for same credentials."""
        client = JiraClientSync(test_credentials)
        http_client_1 = client._get_persistent_client()
        http_client_2 = client._get_persistent_client()
        assert http_client_1 is http_client_2


class TestClientErrorHandling:
    """Tests for client error handling."""

    def test_handle_error_with_timeout(self, test_credentials):
        """Test that timeout errors raise JiraConnectionError."""
        client = JiraClientSync(test_credentials)
        timeout_error = httpx.TimeoutException("Request timed out")

        with pytest.raises(JiraConnectionError) as exc_info:
            client._handle_error(timeout_error)

        assert "timed out" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is timeout_error

    def test_handle_error_with_network_error(self, test_credentials):
        """Test that network errors raise JiraConnectionError."""
        client = JiraClientSync(test_credentials)
        network_error = httpx.NetworkError("Connection failed")

        with pytest.raises(JiraConnectionError) as exc_info:
            client._handle_error(network_error)

        assert "network error" in str(exc_info.value).lower()
        assert exc_info.value.__cause__ is network_error

    def test_handle_error_with_unknown_error(self, test_credentials):
        """Test that unknown errors raise JiraError."""
        client = JiraClientSync(test_credentials)
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

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == ["Error 1", "Error 2"]

    def test_extract_error_messages_from_errors_field(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from errors field."""
        mock_http_response.json.return_value = {
            "errors": {"field1": "Error 1", "field2": "Error 2"}
        }

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert set(messages) == {"Error 1", "Error 2"}

    def test_extract_error_messages_from_message_field(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error message from message field."""
        mock_http_response.json.return_value = {"message": "Single error message"}

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == ["Single error message"]

    def test_extract_error_messages_empty_error_messages_with_field_errors(
        self, test_credentials, mock_http_response
    ):
        """Test that field-level errors are returned when errorMessages is empty."""
        mock_http_response.json.return_value = {
            "errorMessages": [],
            "errors": {"summary": "Field 'summary' is required"},
        }

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == ["Field 'summary' is required"]

    def test_extract_error_messages_both_populated(
        self, test_credentials, mock_http_response
    ):
        """Test that both errorMessages and field errors are collected."""
        mock_http_response.json.return_value = {
            "errorMessages": ["General error"],
            "errors": {"issuetype": "Specify an issue type"},
        }

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert "General error" in messages
        assert "Specify an issue type" in messages
        assert len(messages) == 2

    def test_extract_error_messages_empty_response(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from empty response."""
        mock_http_response.json.return_value = {}

        client = JiraClientSync(test_credentials)
        messages = client._extract_error_messages(mock_http_response)
        assert messages == []

    def test_extract_error_messages_invalid_json(
        self, test_credentials, mock_http_response
    ):
        """Test extracting error messages from invalid JSON."""
        mock_http_response.json.side_effect = ValueError("Invalid JSON")

        client = JiraClientSync(test_credentials)
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
        client = JiraClientSync(test_credentials)

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


class TestRetryOnRateLimit:
    """Tests for automatic retry on 429 rate limit responses."""

    def _make_rate_limit_handler(
        self,
        fail_count: int,
        retry_after: str | None = None,
        rate_limit_reason: str | None = None,
        reset_at: str | None = None,
    ):
        """Create a handler that returns 429 `fail_count` times, then 200."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count <= fail_count:
                headers = {}
                if retry_after:
                    headers["Retry-After"] = retry_after
                if rate_limit_reason:
                    headers["RateLimit-Reason"] = rate_limit_reason
                if reset_at:
                    headers["X-RateLimit-Reset"] = reset_at
                return httpx.Response(
                    429,
                    json={"errorMessages": ["Rate limit exceeded"]},
                    headers=headers,
                )
            return httpx.Response(200, json={"key": "TEST-1"})

        return handler, lambda: call_count

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_succeeds_after_429(self, mock_sleep, mock_uniform, test_credentials):
        """Test that request retries and succeeds after transient 429."""
        handler, get_count = self._make_rate_limit_handler(2)

        client = JiraClientSync(test_credentials, max_retries=4)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            result = client._request_jira("GET", "issue/TEST-1")
            assert result == {"key": "TEST-1"}
            assert get_count() == 3  # 2 failures + 1 success
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_exhausted_raises_rate_limit_error(
        self, mock_sleep, mock_uniform, test_credentials
    ):
        """Test that JiraRateLimitError is raised after all retries exhausted."""
        handler, get_count = self._make_rate_limit_handler(
            10,
            retry_after="5",
            rate_limit_reason="jira-burst-based",
            reset_at="2026-03-06T11:00:00Z",
        )

        client = JiraClientSync(test_credentials, max_retries=3)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            with pytest.raises(JiraRateLimitError) as exc_info:
                client._request_jira("GET", "issue/TEST-1")

            assert exc_info.value.retry_after == 5.0
            assert exc_info.value.rate_limit_reason == "jira-burst-based"
            assert exc_info.value.reset_at == "2026-03-06T11:00:00Z"
            assert get_count() == 4  # 1 initial + 3 retries
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_disabled_with_zero_max_retries(
        self, mock_sleep, mock_uniform, test_credentials
    ):
        """Test that retry is disabled when max_retries=0."""
        handler, get_count = self._make_rate_limit_handler(5)

        client = JiraClientSync(test_credentials, max_retries=0)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            with pytest.raises(JiraRateLimitError):
                client._request_jira("GET", "issue/TEST-1")
            assert get_count() == 1  # No retries
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_respects_retry_after_header(
        self, mock_sleep, mock_uniform, test_credentials
    ):
        """Test that wait time uses Retry-After header when present."""
        handler, _ = self._make_rate_limit_handler(1, retry_after="7")

        client = JiraClientSync(test_credentials, max_retries=2)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            client._request_jira("GET", "issue/TEST-1")
            # With Retry-After=7, additive jitter: 7 + uniform(0, 2.1) = 7 + 1.0 = 8.0
            # Jitter is applied *above* the server minimum to respect Retry-After
            mock_sleep.assert_called_once_with(8.0)
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_uses_exponential_backoff_without_header(
        self, mock_sleep, mock_uniform, test_credentials
    ):
        """Test exponential backoff when no Retry-After header."""
        handler, _ = self._make_rate_limit_handler(2)  # No Retry-After header

        client = JiraClientSync(test_credentials, max_retries=4)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            client._request_jira("GET", "issue/TEST-1")
            # With jitter=1.0: attempt 1 → 5*2^0=5s, attempt 2 → 5*2^1=10s
            calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert calls == [5.0, 10.0]
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    @patch("jira2py.client.client_sync.random.uniform", return_value=1.0)
    @patch("tenacity.nap.time.sleep", return_value=None)
    def test_retry_caps_at_max_delay(self, mock_sleep, mock_uniform, test_credentials):
        """Test that wait time is capped at max_retry_delay."""
        handler, _ = self._make_rate_limit_handler(1, retry_after="120")

        client = JiraClientSync(test_credentials, max_retries=2, max_retry_delay=15.0)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            client._request_jira("GET", "issue/TEST-1")
            # Retry-After=120 but max_retry_delay=15, so capped at 15.0
            mock_sleep.assert_called_once_with(15.0)
        finally:
            client._class_persistent_clients.pop(client._client_key, None)

    def test_non_429_errors_are_not_retried(self, test_credentials):
        """Test that non-429 errors are raised immediately without retry."""
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500, json={"message": "Server error"})

        client = JiraClientSync(test_credentials, max_retries=4)
        client._class_persistent_clients[client._client_key] = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url=f"{test_credentials.url}/rest/api/3",
            auth=httpx.BasicAuth(test_credentials.username, test_credentials.api_token),
        )
        try:
            with pytest.raises(JiraAPIError):
                client._request_jira("GET", "issue/TEST-1")
            assert call_count == 1  # No retries for 500
        finally:
            client._class_persistent_clients.pop(client._client_key, None)
