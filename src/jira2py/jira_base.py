import json
import os
import random
import time
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
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
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
            max_retries: Maximum number of retries for rate-limited requests
            initial_retry_delay: Initial delay in seconds for retry backoff
            max_retry_delay: Maximum delay in seconds for retry backoff
        """
        raw_url = str(jira_url) if jira_url else os.getenv("JIRA_URL", "")
        self._jira_url = raw_url.rstrip("/")
        self._jira_user = jira_user or os.getenv("JIRA_USER")
        self._jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self._raw_response = raw_response
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay
        self._max_retry_delay = max_retry_delay

        if not all([self._jira_url, self._jira_user, self._jira_api_token]):
            raise ValueError(
                "All JIRA credentials must be provided either as parameters or through environment variables "
                "(JIRA_URL, JIRA_USER, JIRA_API_TOKEN)"
            )

        # Create a session for connection reuse
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(
            self._jira_user or "", self._jira_api_token or ""
        )
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def __enter__(self):
        """Enter the runtime context for the Jira client."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context for the Jira client, ensuring the session is closed."""
        self.close()

    def close(self):
        """Close the session and free up resources."""
        if hasattr(self, "_session") and self._session:
            self._session.close()

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
        jitter = random.uniform(0.7, 1.3)
        return delay * jitter

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
                - For other responses, raises ValueError or returns raw response based on raw_response setting

        Raises:
            ValueError: When a non-retryable error occurs or max retries exceeded
        """
        # Validate context_path
        if not context_path or not context_path.strip():
            raise ValueError("context_path cannot be empty")

        # Filter out None values from params and data
        filtered_params = (
            {k: v for k, v in params.items() if v is not None} if params else None
        )
        filtered_data = (
            {k: v for k, v in data.items() if v is not None} if data else None
        )

        # Construct the API URL more robustly
        base_url = self._jira_url.rstrip("/")
        api_path = context_path.strip("/")
        url = f"{base_url}/rest/api/3/{api_path}"

        # Try the request with retries for rate limiting
        retry_count = 0
        while True:
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=filtered_params,
                    data=json.dumps(filtered_data) if filtered_data else None,
                )

                # If raw_response is True, return the raw response object regardless of status code
                if self._raw_response:
                    return response

                # Handle rate limiting (HTTP 429)
                if response.status_code == 429:
                    if retry_count >= self._max_retries:
                        raise ValueError(
                            f"Max retries exceeded for rate-limited request. "
                            f"Jira API error: status_code={response.status_code}, message={response.text}"
                        )

                    # Get retry delay from headers or calculate with backoff
                    retry_after = response.headers.get("Retry-After")
                    delay = self._calculate_retry_delay(retry_count, retry_after)

                    # Also check for beta headers
                    if not retry_after:
                        retry_after = response.headers.get("Beta-Retry-After")
                        if retry_after:
                            delay = self._calculate_retry_delay(
                                retry_count, retry_after
                            )

                    # Wait before retrying
                    time.sleep(delay)
                    retry_count += 1
                    continue

                # Handle successful responses
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 204:
                    return True
                else:
                    # For non-200/204/429 responses, raise an error with structured message
                    raise ValueError(
                        f"Jira API error: status_code={response.status_code}, message={response.text}"
                    )

            except requests.exceptions.RequestException as req_err:
                if self._raw_response:
                    raise req_err
                raise ValueError(f"Request error: {req_err}") from req_err
            except Exception as e:
                if self._raw_response:
                    raise e
                raise ValueError(f"Unexpected error: {e}") from e
