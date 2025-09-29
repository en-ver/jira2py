"""Synchronous Jira API facade."""

from typing import Any

from jira2py.client import JiraClientSync, JiraCredentials

from .issue_comments import IssueComments
from .issue_fields import IssueFields
from .issue_search import IssueSearch
from .issues import Issues
from .jira_api_base import JiraAPIBase


class JiraAPI(JiraAPIBase):
    """Synchronous Jira API facade.

    Provides a unified interface to all Jira API endpoints using synchronous operations.
    This class composes individual API clients and provides a single entry point
    for all Jira operations.

    Example:
        >>> from jira2py import JiraAPI
        >>> api = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
        >>> issue = api.issues.get_issue("PROJ-123")
        >>> fields = api.fields.get_fields()
    """

    def __init__(
        self,
        credentials: JiraCredentials | None = None,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
    ) -> None:
        """Initialize the synchronous Jira API facade.

        Args:
            credentials: JIRA authentication credentials. If None, credentials will be
                created from the provided parameters or environment variables.
            url: Base URL of the JIRA instance. Only used if credentials is None.
            username: JIRA username. Only used if credentials is None.
            api_token: JIRA API token. Only used if credentials is None.
        """
        super().__init__(url, username, api_token)
        # Single shared client for all modules
        self._client = JiraClientSync(self.credentials)

    @property
    def issues(self) -> Issues:
        """Get issues client."""
        return Issues(self._client)

    @property
    def fields(self) -> IssueFields:
        """Get fields client."""
        return IssueFields(self._client)

    @property
    def search(self) -> IssueSearch:
        """Get search client."""
        return IssueSearch(self._client)

    @property
    def comments(self) -> IssueComments:
        """Get comments client."""
        return IssueComments(self._client)

    def __enter__(self) -> "JiraAPI":
        """Enter context manager and delegate to client."""
        self._client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and delegate to client."""
        self._client.__exit__(exc_type, exc_val, exc_tb)
