"""Generic base class for API implementations."""

from abc import ABC
from typing import Any, Generic, TypeVar

from jira2py.client import JiraClientAsync, JiraClientSync

T = TypeVar("T", JiraClientSync, JiraClientAsync)


class ApiBase(Generic[T], ABC):
    """Generic base class for API implementations.

    This class provides a common foundation for both sync and async API implementations,
    following the sans-I/O pattern: it contains business logic and data preparation
    but no actual I/O operations. All I/O is delegated to the injected client.

    This approach:
    - Eliminates code duplication between sync/async implementations
    - Separates business logic from I/O operations
    - Allows thorough testing of logic without network calls
    - Leverages httpx's built-in URL handling (configured with base_url in the client)

    Example:
        >>> class MyAPI(ApiBase[JiraClientSync]):
        ...     def get_item(self, item_id: str) -> dict:
        ...         # Business logic: prepare request configuration
        ...         config = {"method": "GET", "context_path": f"items/{item_id}"}
        ...         # I/O: delegate to client
        ...         return self._client._request_jira(**config)
    """

    def __init__(self, client: T) -> None:
        """Initialize with a client instance.

        Args:
            client: JIRA client instance (sync or async).
                    The client handles all I/O operations via httpx.
        """
        self._client: T = client

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
