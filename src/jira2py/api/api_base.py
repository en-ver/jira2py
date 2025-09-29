"""Generic base class for API implementations."""

from abc import ABC
from typing import Generic, TypeVar

from jira2py.client import JiraClientAsync, JiraClientSync

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class ApiBase(Generic[T], ABC):
    """Generic base class for API implementations.

    This class provides a common foundation for both sync and async API implementations,
    eliminating code duplication through generic programming patterns.
    """

    def __init__(self, client: T) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async)
        """
        self._client: T = client
