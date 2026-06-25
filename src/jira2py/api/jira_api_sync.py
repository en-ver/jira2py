"""Synchronous Jira API facade."""

from functools import cached_property

from jira2py.client import JiraClientSync, JiraCredentials
from jira2py.client.client_sync import _DEFAULT_MAX_RETRIES, _DEFAULT_MAX_RETRY_DELAY

from .attachments import Attachments
from .issue_comments import IssueComments
from .issue_fields import IssueFields
from .issue_links import IssueLinks
from .issue_search import IssueSearch
from .issue_worklogs import IssueWorklogs
from .issues import Issues
from .projects import Projects
from .users import Users


class JiraAPI:
    """Synchronous Jira API facade.

    Provides a unified interface to all Jira API endpoints.
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
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        max_retry_delay: float = _DEFAULT_MAX_RETRY_DELAY,
    ) -> None:
        """Initialize the Jira API facade.

        Args:
            url: Base URL of the JIRA instance.
            username: JIRA username.
            api_token: JIRA API token.
            max_retries: Maximum number of retries on 429 responses. Set to 0 to disable.
                Mirrors the client default ``_DEFAULT_MAX_RETRIES``.
            max_retry_delay: Maximum delay in seconds between retries.
                Mirrors the client default ``_DEFAULT_MAX_RETRY_DELAY``.
        """
        self._credentials = JiraCredentials.create(
            url=url, username=username, api_token=api_token
        )
        self._client = JiraClientSync(
            self._credentials,
            max_retries=max_retries,
            max_retry_delay=max_retry_delay,
        )

    @property
    def credentials(self) -> JiraCredentials:
        """Get the JIRA credentials."""
        return self._credentials

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
    def worklogs(self) -> IssueWorklogs:
        """Get worklogs client."""
        return IssueWorklogs(self._client)

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
