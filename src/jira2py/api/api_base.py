"""Base class for API implementations."""

from typing import Any

from jira2py.client import JiraClientSync

_DEFAULT_PAGE_SIZE = 50


class ApiBase:
    """Base class for API implementations.

    Stores the shared client reference and provides response type-narrowing
    helpers used by all API modules.
    """

    def __init__(self, client: JiraClientSync) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance for making HTTP requests.
        """
        self._client: JiraClientSync = client

    @staticmethod
    def _as_dict(
        result: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Narrow a response to dict, raising TypeError on unexpected types."""
        if isinstance(result, dict):
            return result
        msg = f"Expected dict response, got {type(result).__name__}"
        raise TypeError(msg)

    @staticmethod
    def _as_list(
        result: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Narrow a response to list, raising TypeError on unexpected types."""
        if isinstance(result, list):
            return result
        msg = f"Expected list response, got {type(result).__name__}"
        raise TypeError(msg)
