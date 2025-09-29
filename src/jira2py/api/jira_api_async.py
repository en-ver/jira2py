"""Asynchronous Jira API facade."""

from typing import Any

from .issue_comments import IssueCommentsAsync
from .issue_fields import IssueFieldsAsync
from .issue_search import IssueSearchAsync
from .issues import IssuesAsync
from .jira_api_base import JiraAPIBase
from jira2py.client import JiraClientAsync


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

    def _create_client(self) -> JiraClientAsync:
        """Create the async client instance."""
        return JiraClientAsync(self.credentials)

    @property
    def issues(self) -> IssuesAsync:
        """Get issues client."""
        return IssuesAsync(self._client)

    @property
    def fields(self) -> IssueFieldsAsync:
        """Get fields client."""
        return IssueFieldsAsync(self._client)

    @property
    def search(self) -> IssueSearchAsync:
        """Get search client."""
        return IssueSearchAsync(self._client)

    @property
    def comments(self) -> IssueCommentsAsync:
        """Get comments client."""
        return IssueCommentsAsync(self._client)

    async def __aenter__(self) -> "JiraAPIAsync":
        """Enter async context manager and delegate to client."""
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and delegate to client."""
        await self._client.__aexit__(exc_type, exc_val, exc_tb)
