"""Tests for jira2py exception hierarchy."""

import pytest

from jira2py.exceptions import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)


class TestJiraError:
    """Tests for base JiraError exception."""

    def test_jira_error_is_base_exception(self):
        """Test that JiraError inherits from Exception."""
        assert issubclass(JiraError, Exception)

    def test_jira_error_can_be_raised_and_caught(self):
        """Test that JiraError can be raised and caught."""
        with pytest.raises(JiraError):
            raise JiraError("Test error")

    def test_jira_error_message_attribute(self):
        """Test that JiraError stores message attribute."""
        error = JiraError("Test error message")
        assert error.message == "Test error message"
        assert str(error) == "Test error message"

    def test_jira_error_response_attribute(self):
        """Test that JiraError can store response object."""
        mock_response = None
        error = JiraError("Test error", response=mock_response)
        assert error.response is None

    def test_jira_error_without_response(self):
        """Test that JiraError can be created without response."""
        error = JiraError("Test error")
        assert error.response is None


class TestExceptionInheritance:
    """Tests for exception hierarchy."""

    def test_all_exceptions_inherit_from_jira_error(self):
        """Test that all custom exceptions inherit from JiraError."""
        exceptions = [
            JiraAuthenticationError,
            JiraConnectionError,
            JiraAPIError,
            JiraNotFoundError,
            JiraRateLimitError,
            JiraValidationError,
        ]
        for exc in exceptions:
            assert issubclass(exc, JiraError), (
                f"{exc.__name__} should inherit from JiraError"
            )

    def test_api_error_subclasses_inherit_from_api_error(self):
        """Test that API error subclasses inherit from JiraAPIError."""
        subclasses = [
            JiraNotFoundError,
            JiraRateLimitError,
            JiraValidationError,
        ]
        for exc in subclasses:
            assert issubclass(exc, JiraAPIError), (
                f"{exc.__name__} should inherit from JiraAPIError"
            )
            assert issubclass(exc, JiraError), (
                f"{exc.__name__} should inherit from JiraError"
            )


class TestJiraAuthenticationError:
    """Tests for JiraAuthenticationError."""

    def test_authentication_error_inheritance(self):
        """Test that JiraAuthenticationError inherits from JiraError."""
        assert issubclass(JiraAuthenticationError, JiraError)

    def test_authentication_error_message(self):
        """Test that JiraAuthenticationError stores message correctly."""
        error = JiraAuthenticationError("Invalid credentials")
        assert "credentials" in str(error).lower()

    def test_authentication_error_with_response(self):
        """Test that JiraAuthenticationError can store response."""
        mock_response = None
        error = JiraAuthenticationError("Auth failed", response=mock_response)
        assert error.response is None


class TestJiraConnectionError:
    """Tests for JiraConnectionError."""

    def test_connection_error_inheritance(self):
        """Test that JiraConnectionError inherits from JiraError."""
        assert issubclass(JiraConnectionError, JiraError)

    def test_connection_error_message(self):
        """Test that JiraConnectionError stores message correctly."""
        error = JiraConnectionError("Network error")
        assert "network" in str(error).lower()


class TestJiraAPIError:
    """Tests for JiraAPIError."""

    def test_api_error_inheritance(self):
        """Test that JiraAPIError inherits from JiraError."""
        assert issubclass(JiraAPIError, JiraError)

    def test_api_error_attributes(self):
        """Test that JiraAPIError stores all attributes."""
        import httpx

        mock_response = httpx.Response(500, json={"message": "Server error"})
        error = JiraAPIError(
            "API error",
            status_code=500,
            response=mock_response,
            error_messages=["error1", "error2"],
        )
        assert error.status_code == 500
        assert error.response is mock_response
        assert error.error_messages == ["error1", "error2"]

    def test_api_error_default_error_messages(self):
        """Test that JiraAPIError defaults to empty error messages list."""
        import httpx

        mock_response = httpx.Response(500, json={"message": "Server error"})
        error = JiraAPIError("API error", status_code=500, response=mock_response)
        assert error.error_messages == []


class TestJiraNotFoundError:
    """Tests for JiraNotFoundError."""

    def test_not_found_error_inheritance(self):
        """Test that JiraNotFoundError inherits from JiraAPIError."""
        assert issubclass(JiraNotFoundError, JiraAPIError)
        assert issubclass(JiraNotFoundError, JiraError)

    def test_not_found_error_message(self):
        """Test that JiraNotFoundError stores message correctly."""
        import httpx

        mock_response = httpx.Response(404, json={"message": "Not found"})
        error = JiraNotFoundError(
            "Resource not found", status_code=404, response=mock_response
        )
        assert "not found" in str(error).lower()


class TestJiraRateLimitError:
    """Tests for JiraRateLimitError."""

    def test_rate_limit_error_inheritance(self):
        """Test that JiraRateLimitError inherits from JiraAPIError."""
        assert issubclass(JiraRateLimitError, JiraAPIError)
        assert issubclass(JiraRateLimitError, JiraError)

    def test_rate_limit_error_message(self):
        """Test that JiraRateLimitError stores message correctly."""
        import httpx

        mock_response = httpx.Response(429, json={"message": "Rate limit exceeded"})
        error = JiraRateLimitError(
            "Rate limit exceeded", status_code=429, response=mock_response
        )
        assert "rate limit" in str(error).lower()


class TestJiraValidationError:
    """Tests for JiraValidationError."""

    def test_validation_error_inheritance(self):
        """Test that JiraValidationError inherits from JiraAPIError."""
        assert issubclass(JiraValidationError, JiraAPIError)
        assert issubclass(JiraValidationError, JiraError)

    def test_validation_error_message(self):
        """Test that JiraValidationError stores message correctly."""
        import httpx

        mock_response = httpx.Response(400, json={"message": "Validation failed"})
        error = JiraValidationError(
            "Validation failed", status_code=400, response=mock_response
        )
        assert "validation" in str(error).lower()


class TestExceptionChaining:
    """Tests for exception chaining."""

    def test_exception_chaining_preserves_cause(self):
        """Test that exception chaining preserves the original exception."""
        original_error = ValueError("Original error")
        try:
            try:
                raise original_error
            except ValueError as e:
                raise JiraError("Wrapped error") from e
        except JiraError as exc:
            assert exc.__cause__ is original_error
            assert exc.__cause__ is not None

    def test_exception_chaining_without_from(self):
        """Test that exceptions can be raised without explicit chaining."""
        try:
            raise JiraError("New error")
        except JiraError as exc:
            assert exc.__cause__ is None
