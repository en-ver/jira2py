"""Synchronous Jira API facade."""

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

    @property
    def issues(self) -> Issues:
        """Get issues client."""
        return Issues(self.credentials)

    @property
    def fields(self) -> IssueFields:
        """Get fields client."""
        return IssueFields(self.credentials)

    @property
    def search(self) -> IssueSearch:
        """Get search client."""
        return IssueSearch(self.credentials)

    @property
    def comments(self) -> IssueComments:
        """Get comments client."""
        return IssueComments(self.credentials)
