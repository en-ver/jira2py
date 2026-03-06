"""Synchronous Jira API facade."""

from functools import cached_property

from jira2py.client import JiraClientSync

from .attachments import Attachments
from .issue_comments import IssueComments
from .issue_fields import IssueFields
from .issue_links import IssueLinks
from .issue_search import IssueSearch
from .issues import Issues
from .jira_api_base import _JiraAPIBase
from .projects import Projects
from .users import Users


class JiraAPI(_JiraAPIBase):
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

    def _create_client(self) -> JiraClientSync:
        """Create the sync client instance."""
        return JiraClientSync(self.credentials)

    @cached_property
    def issues(self) -> Issues:
        """Get issues client."""
        return Issues(self._client)

    @cached_property
    def fields(self) -> IssueFields:
        """Get fields client."""
        return IssueFields(self._client)

    @cached_property
    def search(self) -> IssueSearch:
        """Get search client."""
        return IssueSearch(self._client)

    @cached_property
    def comments(self) -> IssueComments:
        """Get comments client."""
        return IssueComments(self._client)

    @cached_property
    def projects(self) -> Projects:
        """Get projects client."""
        return Projects(self._client)

    @cached_property
    def attachments(self) -> Attachments:
        """Get attachments client."""
        return Attachments(self._client)

    @cached_property
    def issue_links(self) -> IssueLinks:
        """Get issue links client."""
        return IssueLinks(self._client)

    @cached_property
    def users(self) -> Users:
        """Get users client."""
        return Users(self._client)
