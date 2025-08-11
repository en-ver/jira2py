"""Unit tests for the IssueSearch class."""

import pytest
import responses
from pydantic import HttpUrl

from jira2py.issue_search import IssueSearch


class TestIssueSearch:
    """Test cases for IssueSearch class."""

    @pytest.fixture
    def issue_search_client(self) -> IssueSearch:
        """Create an IssueSearch client instance for testing."""
        jira_url = HttpUrl("https://test.atlassian.net")
        return IssueSearch(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

    @responses.activate
    def test_enhanced_search_success(self, issue_search_client: IssueSearch) -> None:
        """Test successful issue search."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/search/jql",
            json={
                "issues": [
                    {
                        "id": "10001",
                        "key": "TEST-123",
                        "fields": {"summary": "Test issue 1"},
                    },
                    {
                        "id": "10002",
                        "key": "TEST-124",
                        "fields": {"summary": "Test issue 2"},
                    },
                ],
                "total": 2,
                "startAt": 0,
                "maxResults": 50,
            },
            status=200,
        )

        result = issue_search_client.enhanced_search(jql="project = TEST")

        assert result["total"] == 2
        assert len(result["issues"]) == 2
        assert result["issues"][0]["key"] == "TEST-123"
        assert result["issues"][1]["key"] == "TEST-124"

    @responses.activate
    def test_enhanced_search_with_fields_parameter(
        self, issue_search_client: IssueSearch
    ) -> None:
        """Test issue search with specific fields."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/search/jql",
            json={
                "issues": [
                    {
                        "id": "10001",
                        "key": "TEST-123",
                        "fields": {"summary": "Test issue 1"},
                    }
                ],
                "total": 1,
                "startAt": 0,
                "maxResults": 50,
            },
            status=200,
        )

        result = issue_search_client.enhanced_search(
            jql="project = TEST", fields=["summary"]
        )

        assert result["total"] == 1
        assert result["issues"][0]["fields"]["summary"] == "Test issue 1"
        # Verify the request payload
        assert len(responses.calls) == 1
        request_data = responses.calls[0].request
        assert request_data.body is not None
        assert '"jql": "project = TEST"' in request_data.body
        assert '"fields": ["summary"]' in request_data.body

    @responses.activate
    def test_enhanced_search_with_max_results(
        self, issue_search_client: IssueSearch
    ) -> None:
        """Test issue search with max results parameter."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test.atlassian.net/rest/api/3/search/jql",
            json={"issues": [], "total": 0, "startAt": 0, "maxResults": 10},
            status=200,
        )

        result = issue_search_client.enhanced_search(
            jql="project = TEST", max_results=10
        )

        assert result["maxResults"] == 10
        # Verify the request payload
        assert len(responses.calls) == 1
        request_data = responses.calls[0].request
        assert request_data.body is not None
        assert '"maxResults": 10' in request_data.body
