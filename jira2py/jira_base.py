import json
import os
from abc import ABC
from typing import Any, cast

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

    def _request_jira_list(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Make a request to the JIRA API that returns a list response.

        This method is specifically used when the API endpoint returns a list of items.
        It handles the request and returns the response as a list of dictionaries.

        Args:
            method: HTTP method to use
            context_path: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            list[dict[str, Any]]: The parsed JSON response as a list of dictionaries

        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        response = self._request_jira(method, context_path, params, data)
        return cast(list[dict[str, Any]], response)

    def _request_jira_dict(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the JIRA API that returns a dictionary response.

        This method is specifically used when the API endpoint returns a single object.
        It handles the request and returns the response as a dictionary.

        Args:
            method: HTTP method to use
            context_path: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            dict[str, Any]: The parsed JSON response as a dictionary

        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        response = self._request_jira(method, context_path, params, data)
        return cast(dict[str, Any], response)

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make a request to the JIRA API.

        This is the base method for making HTTP requests to the JIRA API. It returns either
        a dictionary or a list of dictionaries depending on the API endpoint. The methods
        `_request_jira_dict` and `_request_jira_list` are type-specific wrappers that should
        be used when the expected response type is known.

        Args:
            method: HTTP method to use
            context_path: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            dict[str, Any] | list[dict[str, Any]]: The parsed JSON response as either
                a dictionary (for single objects) or a list of dictionaries (for collections)

        Raises:
            httpx.HTTPStatusError: For HTTP error responses
            json.JSONDecodeError: If the response cannot be parsed as JSON
        """
        try:
            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=f"{self._jira_url}/rest/api/{JIRA_API_VERSION}/{context_path.strip('/')}",
                    params=params,
                    json=data,
                    headers={
                        "Accept": "application/json",
                    },
                    auth=httpx.BasicAuth(self._jira_user, self._jira_api_token),
                )

                response.raise_for_status()

                return response.json()

        except httpx.HTTPStatusError as req_err:
            raise req_err
        except json.JSONDecodeError as json_err:
            raise json_err
