"""Asynchronous Jira API facade."""

from functools import cached_property

from jira2py.client import JiraClientAsync

from .attachments import AttachmentsAsync
from .issue_comments import IssueCommentsAsync
from .issue_fields import IssueFieldsAsync
from .issue_links import IssueLinksAsync
from .issue_search import IssueSearchAsync
from .issues import IssuesAsync
from .jira_api_base import _JiraAPIBase
from .projects import ProjectsAsync
from .users import UsersAsync


class JiraAPIAsync(_JiraAPIBase):
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

    @cached_property
    def issues(self) -> IssuesAsync:
        """Get issues client."""
        return IssuesAsync(self._client)

    @cached_property
    def fields(self) -> IssueFieldsAsync:
        """Get fields client."""
        return IssueFieldsAsync(self._client)

    @cached_property
    def search(self) -> IssueSearchAsync:
        """Get search client."""
        return IssueSearchAsync(self._client)

    @cached_property
    def comments(self) -> IssueCommentsAsync:
        """Get comments client."""
        return IssueCommentsAsync(self._client)

    @cached_property
    def projects(self) -> ProjectsAsync:
        """Get projects client."""
        return ProjectsAsync(self._client)

    @cached_property
    def attachments(self) -> AttachmentsAsync:
        """Get attachments client."""
        return AttachmentsAsync(self._client)

    @cached_property
    def issue_links(self) -> IssueLinksAsync:
        """Get issue links client."""
        return IssueLinksAsync(self._client)

    @cached_property
    def users(self) -> UsersAsync:
        """Get users client."""
        return UsersAsync(self._client)
