"""Base class for Jira API facades."""

from abc import ABC, abstractmethod
from typing import Any
from jira2py.client import JiraCredentials


class JiraAPIBase(ABC):
    """Base class for Jira API facades.

    Defines the common interface that all Jira API implementations must provide.
    Handles credential initialization and enforces consistent API structure.
    """

    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
    ):
        """Initialize the base Jira API facade.

        Args:
            url: Base URL of the JIRA instance.
            username: JIRA username.
            api_token: JIRA API token.
        """
        self._credentials = JiraCredentials(
            url=url, username=username, api_token=api_token
        )

    @property
    def credentials(self) -> JiraCredentials:
        """Get the JIRA credentials."""
        return self._credentials

    @property
    @abstractmethod
    def issues(self) -> Any:
        """Get issues client."""
        pass

    @property
    @abstractmethod
    def fields(self) -> Any:
        """Get fields client."""
        pass

    @property
    @abstractmethod
    def search(self) -> Any:
        """Get search client."""
        pass

    @property
    @abstractmethod
    def comments(self) -> Any:
        """Get comments client."""
        pass
