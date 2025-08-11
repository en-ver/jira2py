"""Unit tests for the JiraBase class."""

from unittest.mock import Mock, patch

import pytest
from pydantic import HttpUrl

from jira2py.exceptions import (
    JiraAuthenticationError,
    JiraRequestError,
)
from jira2py.jira_base import JiraBase


class TestJiraBase:
    """Test cases for JiraBase class."""

    def test_init_with_valid_parameters(self) -> None:
        """Test JiraBase initialization with valid parameters."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        assert jira._jira_url == "https://test.atlassian.net"
        assert jira._jira_user == "test@example.com"
        assert jira._jira_api_token == "test-token"

    @patch("os.getenv")
    def test_init_missing_credentials_raises_error(self, mock_getenv: Mock) -> None:
        """Test JiraBase initialization raises error when credentials are missing."""
        # Mock environment variables to return None
        mock_getenv.return_value = None

        jira_url = HttpUrl("https://test.atlassian.net")
        with pytest.raises(
            JiraAuthenticationError, match="All JIRA credentials must be provided"
        ):
            JiraBase(
                jira_url=jira_url,
                jira_user=None,
                jira_api_token="test-token",
            )

    @patch("os.getenv")
    def test_init_with_environment_variables(self, mock_getenv: Mock) -> None:
        """Test JiraBase initialization with environment variables."""
        mock_getenv.side_effect = lambda key, default=None: {
            "JIRA_URL": "https://env-test.atlassian.net",
            "JIRA_USER": "env-user@example.com",
            "JIRA_API_TOKEN": "env-token",
        }.get(key, default)

        jira = JiraBase()

        assert jira._jira_url == "https://env-test.atlassian.net"
        assert jira._jira_user == "env-user@example.com"
        assert jira._jira_api_token == "env-token"

    def test_context_manager(self) -> None:
        """Test JiraBase context manager functionality."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        with patch.object(jira, "close") as mock_close:
            with jira as jira_instance:
                assert jira_instance is jira

            mock_close.assert_called_once()

    def test_close_method(self) -> None:
        """Test JiraBase close method."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        # Create a session first to test closing
        jira._ensure_session()
        assert jira._session is not None

        # Test close method
        jira.close()

        # Verify session is closed and set to None
        assert jira._session is None

    def test_build_api_url(self) -> None:
        """Test _build_api_url method."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        # Test normal path
        url = jira._build_api_url("issue/TEST-123")
        assert url == "https://test.atlassian.net/rest/api/3/issue/TEST-123"

        # Test path with leading/trailing slashes
        url = jira._build_api_url("/issue/TEST-123/")
        assert url == "https://test.atlassian.net/rest/api/3/issue/TEST-123"

        # Test empty path
        with pytest.raises(ValueError, match="context_path cannot be empty"):
            jira._build_api_url("")

        # Test whitespace path
        with pytest.raises(ValueError, match="context_path cannot be empty"):
            jira._build_api_url("   ")

    def test_filter_none_values(self) -> None:
        """Test _filter_none_values method."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        # Test with None values
        data = {"key1": "value1", "key2": None, "key3": "value3", "key4": None}
        filtered = jira._filter_none_values(data)
        assert filtered == {"key1": "value1", "key3": "value3"}

        # Test with no None values
        data = {"key1": "value1", "key2": "value2"}
        filtered = jira._filter_none_values(data)
        assert filtered == data

        # Test with None input
        filtered = jira._filter_none_values(None)
        assert filtered is None

        # Test with empty dict
        filtered = jira._filter_none_values({})
        assert filtered == {}

    def test_calculate_retry_delay(self) -> None:
        """Test _calculate_retry_delay method."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        # Test with retry-after header
        delay = jira._calculate_retry_delay(0, "5.0")
        assert delay == 5.0

        # Test with invalid retry-after header
        delay = jira._calculate_retry_delay(0, "invalid")
        assert delay > 0  # Should fall back to exponential backoff

        # Test exponential backoff
        delay1 = jira._calculate_retry_delay(0)
        delay2 = jira._calculate_retry_delay(1)
        delay3 = jira._calculate_retry_delay(2)

        assert delay2 > delay1  # Should increase with retry count
        assert delay3 > delay2  # Should increase with retry count

    def test_handle_response(self) -> None:
        """Test _handle_response method."""
        jira_url = HttpUrl("https://test.atlassian.net")
        jira = JiraBase(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

        # Mock response for 200 OK
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        result = jira._handle_response(mock_response)
        assert result == {"key": "value"}

        # Mock response for 204 No Content
        mock_response.status_code = 204
        result = jira._handle_response(mock_response)
        assert result is True

        # Mock response for error
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with pytest.raises(JiraRequestError, match="Jira API error: status_code=400"):
            jira._handle_response(mock_response)
