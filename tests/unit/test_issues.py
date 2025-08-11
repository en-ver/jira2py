"""Unit tests for the Issues class."""

import pytest
import responses
from pydantic import HttpUrl

from jira2py.issues import Issues


class TestIssues:
    """Test cases for Issues class."""

    @pytest.fixture
    def issues_client(self) -> Issues:
        """Create a Issues client instance for testing."""
        jira_url = HttpUrl("https://test.atlassian.net")
        return Issues(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

    @responses.activate
    def test_get_issue_success(self, issues_client: Issues) -> None:
        """Test successful retrieval of an issue."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123",
            json={
                "id": "10001",
                "key": "TEST-123",
                "fields": {"summary": "Test issue", "description": "Test description"},
            },
            status=200,
        )

        result = issues_client.get_issue("TEST-123")

        assert result["key"] == "TEST-123"
        assert result["fields"]["summary"] == "Test issue"

    @responses.activate
    def test_get_issue_with_fields_parameter(self, issues_client: Issues) -> None:
        """Test retrieval of an issue with specific fields."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123",
            json={
                "id": "10001",
                "key": "TEST-123",
                "fields": {"summary": "Test issue"},
            },
            status=200,
        )

        result = issues_client.get_issue("TEST-123", fields="summary")

        assert result["key"] == "TEST-123"
        assert result["fields"]["summary"] == "Test issue"
        # Verify the request was made with the correct parameters
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert request_url is not None
        assert "fields=summary" in request_url

    @responses.activate
    def test_get_changelogs_success(self, issues_client: Issues) -> None:
        """Test successful retrieval of issue changelogs."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123/changelog",
            json={
                "startAt": 0,
                "maxResults": 50,
                "total": 1,
                "isLast": True,
                "values": [
                    {
                        "id": "10001",
                        "author": {"name": "testuser"},
                        "created": "2023-01-01T00:00:00.000+0000",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "Open",
                                "toString": "In Progress",
                            }
                        ],
                    }
                ],
            },
            status=200,
        )

        result = issues_client.get_changelogs("TEST-123")

        assert result["total"] == 1
        assert len(result["values"]) == 1
        assert result["values"][0]["id"] == "10001"
        assert result["values"][0]["items"][0]["field"] == "status"

    @responses.activate
    def test_edit_issue_success(self, issues_client: Issues) -> None:
        """Test successful editing of an issue."""
        # Mock the API response
        responses.add(
            responses.PUT,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123",
            json={
                "id": "10001",
                "key": "TEST-123",
                "fields": {"summary": "Updated test issue"},
            },
            status=200,
        )

        result = issues_client.edit_issue(
            issue_id="TEST-123", fields={"summary": "Updated test issue"}
        )

        assert result["key"] == "TEST-123"
        assert result["fields"]["summary"] == "Updated test issue"
