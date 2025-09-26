import json
import os
from abc import ABC
from typing import Any, overload

import httpx
from pydantic import EmailStr, HttpUrl, validate_call

JIRA_API_VERSION = 3


class JiraBase(ABC):
    """Base class for JIRA operations providing authentication and common functionality.

    This class provides standardized JIRA authentication and core operations.
    Implementations can extend this to create specific JIRA clients with custom behaviors.

    Environment Variables:
        JIRA_URL: The URL of your JIRA instance.
        JIRA_USER: Your JIRA username (email).
        JIRA_API_TOKEN: Your JIRA API token.

    Raises:
        ValueError: If any of the required credentials are missing from both
                   constructor parameters and environment variables.
    """

    @validate_call
    def __init__(
        self,
        jira_url: HttpUrl | None = None,
        jira_user: EmailStr | None = None,
        jira_api_token: str | None = None,
    ):
        """Initialize JIRA client with authentication credentials.

        Args:
            jira_url: The URL of your JIRA instance. If not provided,
                      will look for JIRA_URL environment variable.
            jira_user: Your JIRA username (email). If not provided,
                       will look for JIRA_USER environment variable.
            jira_api_token: Your JIRA API token. If not provided,
                            will look for JIRA_API_TOKEN environment variable.
        """
        raw_url = str(jira_url) if jira_url else os.getenv("JIRA_URL", "")
        self._jira_url = raw_url.rstrip("/")
        self._jira_user = jira_user or os.getenv("JIRA_USER", "")
        self._jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN", "")

        if not all([self._jira_url, self._jira_user, self._jira_api_token]):
            raise ValueError(
                "All JIRA credentials must be provided either as parameters or through environment variables "
                "(JIRA_URL, JIRA_USER, JIRA_API_TOKEN)"
            )

        # Store client configuration for session reuse
        self._client = None
        self._client_config = {
            "base_url": f"{self._jira_url}/rest/api/{JIRA_API_VERSION}",
            "headers": {"Accept": "application/json"},
            "auth": httpx.BasicAuth(self._jira_user, self._jira_api_token),
        }

    def __enter__(self):
        """Enter context and create HTTP client session."""
        if self._client is not None:
            raise RuntimeError("Jira client session is already active")
        
        self._client = httpx.Client(**self._client_config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and cleanup HTTP client session."""
        if self._client:
            self._client.close()
            self._client = None

    @overload
    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        response_type: type[list],
    ) -> list[dict[str, Any]]:
        """Overload for when we expect a list response."""
        ...

    @overload
    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        response_type: type[dict],
    ) -> dict[str, Any]:
        """Overload for when we expect a dict response."""
        ...

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        *,
        response_type: type[list] | type[dict] = dict,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a request to the JIRA API.

        This is the base method for making HTTP requests to the JIRA API. It returns either
        a dictionary or a list of dictionaries depending on the API endpoint.

        Args:
            method: HTTP method to use
            context_path: API endpoint path
            params: Query parameters
            data: Request body data
            response_type: Type of response expected (dict or list)

        Returns:
            dict[str, Any] | list[dict[str, Any]]: The parsed JSON response as either
                a dictionary (for single objects) or a list of dictionaries (for collections)

        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        try:
            if self._client is None:
                # Fallback to single-use client (maintains backward compatibility)
                with httpx.Client(**self._client_config) as client:
                    response = client.request(
                        method=method,
                        url=context_path.lstrip('/'),
                        params=params,
                        json=data,
                    )
            else:
                # Use the session client
                response = self._client.request(
                    method=method,
                    url=context_path.lstrip('/'),
                    params=params,
                    json=data,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as req_err:
            raise req_err
        except json.JSONDecodeError as json_err:
            raise json_err
