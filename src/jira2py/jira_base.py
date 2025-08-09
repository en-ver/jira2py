import json
import os
from abc import ABC
from typing import Any

import requests
from pydantic import EmailStr, HttpUrl, validate_call
from requests.auth import HTTPBasicAuth


class JiraBase(ABC):
    """Base class for JIRA operations providing authentication and common functionality.

    Provides standardized JIRA authentication and core operations. Implementations
    can extend this to create specific JIRA clients with custom behaviors.

    Environment Variables:
        JIRA_URL: The URL of your JIRA instance
        JIRA_USER: Your JIRA username (email)
        JIRA_API_TOKEN: Your JIRA API token

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
        raw_response: bool | None = False,
    ):
        """Initialize JIRA client with authentication credentials.

        Args:
            jira_url: The URL of your JIRA instance. If not provided,
                     will look for JIRA_URL environment variable.
            jira_user: Your JIRA username (email). If not provided,
                      will look for JIRA_USER environment variable.
            jira_api_token: Your JIRA API token. If not provided,
                           will look for JIRA_API_TOKEN environment variable.
            raw_response: If True, returns raw response objects from the API
                         instead of handling errors internally.
        """
        raw_url = str(jira_url) if jira_url else os.getenv("JIRA_URL", "")
        self._jira_url = raw_url.rstrip("/")
        self._jira_user = jira_user or os.getenv("JIRA_USER")
        self._jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self._raw_response = raw_response

        if not all([self._jira_url, self._jira_user, self._jira_api_token]):
            raise ValueError(
                "All JIRA credentials must be provided either as parameters or through environment variables "
                "(JIRA_URL, JIRA_USER, JIRA_API_TOKEN)"
            )

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the JIRA API.

        Args:
            method: HTTP method to use
            context_path: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            If raw_response is True, returns the raw requests.Response object.
            Otherwise:
                - For 200 responses, returns the parsed JSON response
                - For 204 responses, returns True
                - For other responses, raises ValueError or returns raw response based on raw_response setting
        """
        try:
            # Validate context_path
            if not context_path or not context_path.strip():
                raise ValueError("context_path cannot be empty")
            
            # Construct the API URL more robustly
            base_url = self._jira_url.rstrip("/")
            api_path = context_path.strip("/")
            url = f"{base_url}/rest/api/3/{api_path}"
            
            response = requests.request(
                method=method,
                url=url,
                params=params,
                data=json.dumps(data) if data else None,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                auth=HTTPBasicAuth(self._jira_user or "", self._jira_api_token or ""),
            )

            # If raw_response is True, return the raw response object regardless of status code
            if self._raw_response:
                return response

            # Handle specific status codes when not in raw_response mode
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return True
            else:
                # For non-200/204 responses, raise an error
                raise ValueError(
                    f"HTTP error occurred: {response.status_code} - {response.text}"
                )

        except requests.exceptions.RequestException as req_err:
            if self._raw_response:
                raise req_err
            raise ValueError(f"Request error: {req_err}") from req_err
        except Exception as e:
            if self._raw_response:
                raise e
            raise ValueError(f"Unexpected error: {e}") from e
