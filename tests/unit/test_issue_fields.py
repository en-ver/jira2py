"""Unit tests for the IssueFields class."""

import pytest
import responses
from pydantic import HttpUrl

from jira2py.issue_fields import IssueFields


class TestIssueFields:
    """Test cases for IssueFields class."""

    @pytest.fixture
    def issue_fields_client(self) -> IssueFields:
        """Create an IssueFields client instance for testing."""
        jira_url = HttpUrl("https://test.atlassian.net")
        return IssueFields(
            jira_url=jira_url, jira_user="test@example.com", jira_api_token="test-token"
        )

    @responses.activate
    def test_get_fields_success(self, issue_fields_client: IssueFields) -> None:
        """Test successful retrieval of issue fields."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test.atlassian.net/rest/api/3/field",
            json=[
                {
                    "id": "summary",
                    "name": "Summary",
                    "custom": False,
                    "orderable": True,
                    "navigable": True,
                    "searchable": True,
                    "clauseNames": ["summary"],
                },
                {
                    "id": "customfield_10001",
                    "name": "Story Points",
                    "custom": True,
                    "orderable": True,
                    "navigable": True,
                    "searchable": True,
                    "clauseNames": ["cf[10001]", "Story Points"],
                },
            ],
            status=200,
        )

        result = issue_fields_client.get_fields()

        assert len(result) == 2
        assert result[0]["id"] == "summary"
        assert result[0]["name"] == "Summary"
        assert result[1]["id"] == "customfield_10001"
        assert result[1]["name"] == "Story Points"
        assert result[1]["custom"] is True
