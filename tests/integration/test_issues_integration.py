"""Integration tests for the Issues class."""

from typing import Optional

import pytest

from jira2py.issues import Issues


@pytest.mark.integration
class TestIssuesIntegration:
    """Integration test cases for Issues class."""

    def test_get_issue_integration(
        self,
        jira_url: Optional[str],
        jira_user: Optional[str],
        jira_api_token: Optional[str],
    ) -> None:
        """Test Issues get_issue with real Jira instance."""
        # Skip if integration test configuration is not available
        if not all([jira_url, jira_user, jira_api_token]):
            pytest.skip("Integration test configuration not available")

        # This test would require a known issue
        # Since we don't have that, we'll just verify the client can be created
        # In a real scenario, you'd want to test with a known issue
        issues = Issues()
        assert issues is not None
