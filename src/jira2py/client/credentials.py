"""JIRA credentials management."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class JiraCredentials:
    """Container for JIRA authentication data.

    This class provides a type-safe way to store and manage JIRA credentials.
    It supports both explicit credential passing and automatic environment variable loading.

    Environment Variables:
        JIRA_URL: The URL of your JIRA instance.
        JIRA_USER: Your JIRA username (email).
        JIRA_API_TOKEN: Your JIRA API token.

    Args:
        url: Base URL of the JIRA instance (e.g., "https://mycompany.atlassian.net")
            If not provided, will be loaded from JIRA_URL environment variable.
        username: JIRA username (typically an email address)
            If not provided, will be loaded from JIRA_USER environment variable.
        api_token: JIRA API token or password (hidden from repr)
            If not provided, will be loaded from JIRA_API_TOKEN environment variable.

    Raises:
        ValueError: If any required credentials are missing or invalid.
    """

    url: str | None = None
    username: str | None = None
    api_token: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate credentials after initialization."""
        # Auto-detect missing values from environment
        final_url = self.url or os.getenv("JIRA_URL", "").strip()
        final_username = self.username or os.getenv("JIRA_USER", "").strip()
        final_token = self.api_token or os.getenv("JIRA_API_TOKEN", "").strip()

        # Update the frozen dataclass with resolved values
        object.__setattr__(self, "url", final_url)
        object.__setattr__(self, "username", final_username)
        object.__setattr__(self, "api_token", final_token)

        # Validate credentials
        if not self.url:
            raise ValueError("JIRA URL is required")
        if not self.username:
            raise ValueError("JIRA username is required")
        if not self.api_token:
            raise ValueError("JIRA API token is required")

        # Validate URL format
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("JIRA URL must start with http:// or https://")

        # Clean URL by removing trailing slashes
        object.__setattr__(self, "url", self.url.rstrip("/"))

    @property
    def base_url(self) -> str:
        """Get the base API URL for these credentials.

        Returns:
            str: Base URL for JIRA API requests.
        """
        return f"{self.url}/rest/api/3"
