"""Unit tests for the IssueComments class."""

import pytest
import responses
from pydantic import HttpUrl

from jira2py.issue_comments import IssueComments


class TestIssueComments:
    """Test cases for IssueComments class."""

    @pytest.fixture
    def issue_comments_client(self) -> IssueComments:
        """Create an IssueComments client instance for testing."""
        jira_url = HttpUrl("https://test.atlassian.net")
        return IssueComments(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

    @responses.activate
    def test_get_comments_success(self, issue_comments_client: IssueComments) -> None:
        """Test successful retrieval of issue comments."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123/comment",
            json={
                "comments": [
                    {
                        "id": "10001",
                        "author": {"name": "testuser"},
                        "body": "This is a test comment",
                        "created": "2023-01-01T00:00:00.000+0000",
                    },
                    {
                        "id": "10002",
                        "author": {"name": "testuser2"},
                        "body": "This is another test comment",
                        "created": "2023-01-02T00:00:00.000+0000",
                    },
                ],
                "total": 2,
                "startAt": 0,
                "maxResults": 100,
            },
            status=200,
        )

        result = issue_comments_client.get_comments("TEST-123")

        assert result["total"] == 2
        assert len(result["comments"]) == 2
        assert result["comments"][0]["id"] == "10001"
        assert result["comments"][0]["body"] == "This is a test comment"
        assert result["comments"][1]["id"] == "10002"
        assert result["comments"][1]["body"] == "This is another test comment"

    @responses.activate
    def test_get_comments_with_pagination(
        self, issue_comments_client: IssueComments
    ) -> None:
        """Test retrieval of issue comments with pagination parameters."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123/comment",
            json={
                "comments": [
                    {
                        "id": "10003",
                        "author": {"name": "testuser"},
                        "body": "This is a paginated comment",
                        "created": "2023-01-03T00:00:00.000+0000",
                    }
                ],
                "total": 1,
                "startAt": 10,
                "maxResults": 50,
            },
            status=200,
        )

        result = issue_comments_client.get_comments(
            issue_id="TEST-123", start_at=10, max_results=50
        )

        assert result["startAt"] == 10
        assert result["maxResults"] == 50
        assert result["comments"][0]["id"] == "10003"
        # Verify the request parameters
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert request_url is not None
        assert "startAt=10" in request_url
        assert "maxResults=50" in request_url

    @responses.activate
    def test_get_comments_with_order_by(
        self, issue_comments_client: IssueComments
    ) -> None:
        """Test retrieval of issue comments with order by parameter."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/issue/TEST-123/comment",
            json={"comments": [], "total": 0, "startAt": 0, "maxResults": 100},
            status=200,
        )

        # Just verify the method call works without error
        issue_comments_client.get_comments(issue_id="TEST-123", order_by="-created")

        # Verify the request parameters
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert request_url is not None
        assert "orderby=-created" in request_url
