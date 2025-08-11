"""Integration tests for the JiraBase class."""

from typing import Optional

import pytest

from jira2py.jira_base import JiraBase


@pytest.mark.integration
class TestJiraBaseIntegration:
    """Integration test cases for JiraBase class."""

    def test_init_with_environment_variables(
        self,
        jira_url: Optional[str],
        jira_user: Optional[str],
        jira_api_token: Optional[str],
    ) -> None:
        """Test JiraBase initialization with environment variables."""
        # Skip if integration test configuration is not available
        if not all([jira_url, jira_user, jira_api_token]):
            pytest.skip("Integration test configuration not available")

        jira = JiraBase()

        assert jira._jira_url == jira_url.rstrip("/") if jira_url else ""
        assert jira._jira_user == jira_user
        assert jira._jira_api_token == jira_api_token
