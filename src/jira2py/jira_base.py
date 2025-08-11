import json
import os
import random
import time
from abc import ABC
from typing import Any, Optional, TypeVar

import requests
from pydantic import EmailStr, HttpUrl, validate_call
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from .exceptions import (
    JiraAuthenticationError,
    JiraRateLimitError,
    JiraRequestError,
)

# Constants
HTTP_OK = 200
HTTP_NO_CONTENT = 204
HTTP_TOO_MANY_REQUESTS = 429
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRY_DELAY = 60.0
DEFAULT_JITTER_MIN = 0.7
DEFAULT_JITTER_MAX = 1.3
API_VERSION = "3"
RETRY_AFTER_HEADER = "Retry-After"
BETA_RETRY_AFTER_HEADER = "Beta-Retry-After"

__all__ = ["JiraBase"]

# Type variable for preserving specific class types
T = TypeVar("T", bound="JiraBase")


class JiraBase(ABC):
    """Base class for JIRA operations providing authentication and common functionality.

    Provides standardized JIRA authentication and core operations. Implementations
    can extend this to create specific JIRA clients with custom behaviors.

    Environment Variables:
        JIRA_URL: The URL of your JIRA instance
        JIRA_USER: Your JIRA username (email)
        JIRA_API_TOKEN: Your JIRA API token

    Raises:
        JiraAuthenticationError: If any of the required credentials are missing from both
                                constructor parameters and environment variables.
    """

    @validate_call
    def __init__(
        self,
        jira_url: HttpUrl | None = None,
        jira_user: EmailStr | None = None,
        jira_api_token: str | None = None,
        raw_response: bool = False,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ) -> None:
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
            max_retries: Maximum number of retries for rate-limited requests
            initial_retry_delay: Initial delay in seconds for retry backoff
            max_retry_delay: Maximum delay in seconds for retry backoff

        Raises:
            JiraAuthenticationError: If authentication credentials are missing.
        """
        self._jira_url = self._get_jira_url(jira_url)
        self._jira_user = jira_user or os.getenv("JIRA_USER")
        self._jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self._raw_response = raw_response
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay
        self._max_retry_delay = max_retry_delay
        self._session: Optional[requests.Session] = None

        self._validate_credentials()

    def __enter__(self: T) -> T:
        """Enter the runtime context for the Jira client."""
        self._ensure_session()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the runtime context for the Jira client, ensuring the session is closed."""
        self.close()

    def close(self) -> None:
        """Close the session and free up resources."""
        if self._session:
            self._session.close()
            self._session = None

    def _ensure_session(self) -> requests.Session:
        """Ensure session is available, creating it if necessary."""
        if self._session is None:
            self._session = requests.Session()

            # Set authentication
            # Ensure credentials are not None before creating HTTPBasicAuth
            if self._jira_user is not None and self._jira_api_token is not None:
                self._session.auth = HTTPBasicAuth(
                    self._jira_user, self._jira_api_token
                )
            else:
                raise JiraAuthenticationError(
                    "JIRA user and API token must be provided for authentication"
                )

            # Set default headers
            self._session.headers.update(
                {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )

            # Configure retries
            if self._max_retries > 0:
                retry_strategy = Retry(
                    total=self._max_retries,
                    status_forcelist=[429, 500, 502, 503, 504],
                    backoff_factor=1,
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self._session.mount("http://", adapter)
                self._session.mount("https://", adapter)

        return self._session

    def _get_jira_url(self, jira_url: HttpUrl | None) -> str:
        """Get JIRA URL from parameter or environment variable."""
        raw_url = str(jira_url) if jira_url else os.getenv("JIRA_URL", "")
        return raw_url.rstrip("/")

    def _validate_credentials(self) -> None:
        """Validate that all required credentials are provided."""
        if not all([self._jira_url, self._jira_user, self._jira_api_token]):
            raise JiraAuthenticationError(
                "All JIRA credentials must be provided either as parameters or through environment variables "
                "(JIRA_URL, JIRA_USER, JIRA_API_TOKEN)"
            )

    def _calculate_retry_delay(
        self, retry_count: int, retry_after_header: str | None = None
    ) -> float:
        """Calculate the delay before retrying a rate-limited request.

        Args:
            retry_count: Current retry attempt number (0-indexed)
            retry_after_header: Value of Retry-After header if present

        Returns:
            Delay in seconds before next retry
        """
        # If server provides a retry-after header, use it
        if retry_after_header:
            try:
                return float(retry_after_header)
            except (ValueError, TypeError):
                pass

        # Exponential backoff with jitter
        delay = min(self._initial_retry_delay * (2**retry_count), self._max_retry_delay)

        # Add jitter to prevent thundering herd
        jitter = random.uniform(DEFAULT_JITTER_MIN, DEFAULT_JITTER_MAX)
        return delay * jitter

    def _build_api_url(self, context_path: str) -> str:
        """Build the complete API URL from base URL and context path.

        Args:
            context_path: The API endpoint path

        Returns:
            Complete API URL

        Raises:
            ValueError: If context_path is empty or invalid
        """
        if not context_path or not context_path.strip():
            raise ValueError("context_path cannot be empty")

        api_path = context_path.strip("/")
        return f"{self._jira_url}/rest/api/{API_VERSION}/{api_path}"

    def _filter_none_values(self, data: dict[str, Any] | None) -> dict[str, Any] | None:
        """Filter out None values from a dictionary.

        Args:
            data: Dictionary to filter

        Returns:
            Filtered dictionary with None values removed, or None if input is None
        """
        if data is None:
            return None
        return {k: v for k, v in data.items() if v is not None}

    def _handle_rate_limiting(
        self, response: requests.Response, retry_count: int
    ) -> float:
        """Handle rate limiting by calculating retry delay.

        Args:
            response: The HTTP response that triggered rate limiting
            retry_count: Current retry attempt number

        Returns:
            Delay in seconds before next retry

        Raises:
            JiraRateLimitError: If max retries exceeded
        """
        if retry_count >= self._max_retries:
            raise JiraRateLimitError(
                f"Max retries exceeded for rate-limited request. "
                f"Jira API error: status_code={response.status_code}, message={response.text}"
            )

        # Get retry delay from headers or calculate with backoff
        retry_after = response.headers.get(RETRY_AFTER_HEADER)
        if not retry_after:
            retry_after = response.headers.get(BETA_RETRY_AFTER_HEADER)

        return self._calculate_retry_delay(retry_count, retry_after)

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle HTTP response and return appropriate data.

        Args:
            response: The HTTP response to handle

        Returns:
            Parsed response data or raw response object

        Raises:
            JiraRequestError: If the response indicates an error
        """
        if response.status_code == HTTP_OK:
            return response.json()
        elif response.status_code == HTTP_NO_CONTENT:
            return True
        else:
            raise JiraRequestError(
                f"Jira API error: status_code={response.status_code}, message={response.text}"
            )

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make a request to the JIRA API with rate limiting support.

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
                - For other responses, raises JiraRequestError

        Raises:
            JiraRequestError: When a non-retryable error occurs
            JiraRateLimitError: When max retries exceeded for rate limiting
        """
        session = self._ensure_session()

        # Build the complete API URL using helper method
        url = self._build_api_url(context_path)

        # Filter out None values from params and data
        filtered_params = self._filter_none_values(params)
        filtered_data = self._filter_none_values(data)

        # Try the request with retries for rate limiting
        retry_count = 0
        while True:
            try:
                response = session.request(
                    method=method,
                    url=url,
                    params=filtered_params,
                    data=json.dumps(filtered_data) if filtered_data else None,
                )

                # If raw_response is True, return the raw response object regardless of status code
                if self._raw_response:
                    return response

                # Handle rate limiting (HTTP 429)
                if response.status_code == HTTP_TOO_MANY_REQUESTS:
                    if retry_count >= self._max_retries:
                        raise JiraRateLimitError(
                            f"Max retries exceeded for rate-limited request. "
                            f"Jira API error: status_code={response.status_code}, message={response.text}"
                        )
                    delay = self._calculate_retry_delay(
                        retry_count, response.headers.get("Retry-After")
                    )
                    time.sleep(delay)
                    retry_count += 1
                    continue

                # Handle other responses
                return self._handle_response(response)

            except requests.exceptions.RequestException as req_err:
                if self._raw_response:
                    raise req_err
                raise JiraRequestError(f"Request error: {req_err}") from req_err
            except Exception as e:
                if self._raw_response:
                    raise e
                raise JiraRequestError(f"Unexpected error: {e}") from e
