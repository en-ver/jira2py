"""Asynchronous Jira API facade."""

from .issue_comments import IssueCommentsAsync
from .issue_fields import IssueFieldsAsync
from .issue_search import IssueSearchAsync
from .issues import IssuesAsync
from .jira_api import JiraAPIBase


class JiraAPIAsync(JiraAPIBase):
    """Asynchronous Jira API facade.

    Provides a unified interface to all Jira API endpoints using asynchronous operations.
    This class composes individual API clients and provides a single entry point
    for all Jira operations.

    Example:
        >>> from jira2py import JiraAPIAsync
        >>> async with JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token") as api:
        ...     issue = await api.issues.get_issue("PROJ-123")
        ...     fields = await api.fields.get_fields()
    """

    @property
    def issues(self) -> IssuesAsync:
        """Get issues client."""
        return IssuesAsync(self.credentials)

    @property
    def fields(self) -> IssueFieldsAsync:
        """Get fields client."""
        return IssueFieldsAsync(self.credentials)

    @property
    def search(self) -> IssueSearchAsync:
        """Get search client."""
        return IssueSearchAsync(self.credentials)

    @property
    def comments(self) -> IssueCommentsAsync:
        """Get comments client."""
        return IssueCommentsAsync(self.credentials)

    async def __aenter__(self) -> "JiraAPIAsync":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and cleanup resources."""
        # Note: Individual clients manage their own resources
        pass
