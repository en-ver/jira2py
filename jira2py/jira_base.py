import requests, json, os
from requests.auth import HTTPBasicAuth
from abc import ABC
from pydantic import EmailStr, HttpUrl, validate_call, ValidationError
from typing import Optional


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
        self._jira_user = jira_user or os.getenv("JIRA_USER")
        self._jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")

        if not all([self._jira_url, self._jira_user, self._jira_api_token]):
            raise ValueError(
                "All JIRA credentials must be provided either as parameters or through environment variables "
                "(JIRA_URL, JIRA_USER, JIRA_API_TOKEN)"
            )

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict | None = None,
        data: dict | None = None,
    ):

        try:
            response = requests.request(
                method=method,
                url=f"{self._jira_url}/rest/api/3/{context_path.strip("/")}",
                params=params,
                data=json.dumps(data) if data else None,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                auth=HTTPBasicAuth(self._jira_user, self._jira_api_token),
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise ValueError(f"HTTP error occurred: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            raise ValueError(f"Request error: {req_err}") from req_err
        except Exception as e:
            raise ValueError(f"Unexpected error: {e}") from e
