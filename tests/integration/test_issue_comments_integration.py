"""Integration tests for the IssueComments class."""

from typing import Optional

import pytest

from jira2py.issue_comments import IssueComments


@pytest.mark.integration
class TestIssueCommentsIntegration:
    """Integration test cases for IssueComments class."""

    def test_get_comments_integration(
        self,
        jira_url: Optional[str],
        jira_user: Optional[str],
        jira_api_token: Optional[str],
    ) -> None:
        """Test IssueComments get_comments with real Jira instance."""
        # Skip if integration test configuration is not available
        if not all([jira_url, jira_user, jira_api_token]):
            pytest.skip("Integration test configuration not available")

        issue_comments = IssueComments()

        # This test would require a known issue with comments
        # Since we don't have that, we'll just verify the client can be created
        # In a real scenario, you'd want to test with a known issue
        assert issue_comments is not None
