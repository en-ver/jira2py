"""JIRA credentials management."""

import os
from dataclasses import dataclass, field
from typing import Self


@dataclass(frozen=True)
class JiraCredentials:
    """Container for JIRA authentication data.

    This class provides a type-safe way to store and manage JIRA credentials.
    Use the ``create`` classmethod to construct instances with automatic
    environment variable fallback and validation.

    Environment Variables:
        JIRA_URL: The URL of your JIRA instance.
        JIRA_USER: Your JIRA username (email).
        JIRA_API_TOKEN: Your JIRA API token.

    Example:
        >>> creds = JiraCredentials.create(
        ...     url="https://mycompany.atlassian.net",
        ...     username="user@example.com",
        ...     api_token="token",
        ... )

        >>> # Or load entirely from environment variables:
        >>> creds = JiraCredentials.create()
    """

    url: str
    username: str
    api_token: str = field(repr=False)

    @classmethod
    def create(
        cls,
        url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
    ) -> Self:
        """Create credentials with environment variable fallback.

        Args:
            url: Base URL of the JIRA instance (e.g., "https://mycompany.atlassian.net").
                Falls back to JIRA_URL environment variable.
            username: JIRA username (typically an email address).
                Falls back to JIRA_USER environment variable.
            api_token: JIRA API token or password.
                Falls back to JIRA_API_TOKEN environment variable.

        Returns:
            Validated JiraCredentials instance.

        Raises:
            ValueError: If any required credentials are missing or invalid.
        """
        final_url = (url or os.getenv("JIRA_URL", "")).strip()
        final_username = (username or os.getenv("JIRA_USER", "")).strip()
        final_token = (api_token or os.getenv("JIRA_API_TOKEN", "")).strip()

        if not final_url:
            raise ValueError("JIRA URL is required")
        if not final_username:
            raise ValueError("JIRA username is required")
        if not final_token:
            raise ValueError("JIRA API token is required")

        if not final_url.startswith(("http://", "https://")):
            raise ValueError("JIRA URL must start with http:// or https://")

        return cls(
            url=final_url.rstrip("/"),
            username=final_username,
            api_token=final_token,
        )
