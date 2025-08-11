"""Integration tests for the IssueSearch class."""

from typing import Optional

import pytest

from jira2py.issue_search import IssueSearch


@pytest.mark.integration
class TestIssueSearchIntegration:
    """Integration test cases for IssueSearch class."""

    def test_enhanced_search_integration(
        self,
        jira_url: Optional[str],
        jira_user: Optional[str],
        jira_api_token: Optional[str],
    ) -> None:
        """Test IssueSearch enhanced_search with real Jira instance."""
        # Skip if integration test configuration is not available
        if not all([jira_url, jira_user, jira_api_token]):
            pytest.skip("Integration test configuration not available")

        issue_search = IssueSearch()

        # Perform a simple search
        result = issue_search.enhanced_search(jql="project IS NOT EMPTY", max_results=5)

        # Verify we got a response with the expected structure
        assert "issues" in result
        # The response may have different fields depending on the API version
        # but should at least have the issues array
        assert isinstance(result["issues"], list)
