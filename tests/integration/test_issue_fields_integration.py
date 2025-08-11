"""Integration tests for the IssueFields class."""

from typing import Optional

import pytest

from jira2py.issue_fields import IssueFields


@pytest.mark.integration
class TestIssueFieldsIntegration:
    """Integration test cases for IssueFields class."""

    def test_get_fields_integration(
        self,
        jira_url: Optional[str],
        jira_user: Optional[str],
        jira_api_token: Optional[str],
    ) -> None:
        """Test IssueFields get_fields with real Jira instance."""
        # Skip if integration test configuration is not available
        if not all([jira_url, jira_user, jira_api_token]):
            pytest.skip("Integration test configuration not available")

        issue_fields = IssueFields()

        # Get fields from the real Jira instance
        result = issue_fields.get_fields()

        # Verify we got a response with the expected structure
        assert isinstance(result, list)
        if len(result) > 0:
            # Check that the first field has the expected structure
            first_field = result[0]
            assert "id" in first_field
            assert "name" in first_field
            assert "custom" in first_field
