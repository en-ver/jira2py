"""JIRA credentials management."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

_REQUIRED_CREDENTIAL_FIELDS = ("url", "username", "api_token")


def _load_credentials_file(
    credentials_file: str | os.PathLike[str],
) -> dict[str, str]:
    """Load and validate credentials from a JSON file."""
    path = Path(credentials_file).expanduser()

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Failed to read JIRA credentials file: {path}") from exc

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JIRA credentials file is not valid JSON: {path}") from exc

    if not isinstance(payload, Mapping):
        raise ValueError(
            "JIRA credentials file must contain a JSON object with "
            "url, username, and api_token fields"
        )

    loaded: dict[str, str] = {}
    for field_name in _REQUIRED_CREDENTIAL_FIELDS:
        raw_value = payload.get(field_name)
        if not isinstance(raw_value, str) or not raw_value.strip():
            raise ValueError(
                "JIRA credentials file must contain non-empty string fields: "
                "url, username, api_token"
            )
        loaded[field_name] = raw_value.strip()

    return loaded


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
        *,
        credentials_file: str | os.PathLike[str] | None = None,
    ) -> Self:
        """Create credentials with explicit, file, and environment fallbacks.

        Args:
            url: Base URL of the JIRA instance (e.g., "https://mycompany.atlassian.net").
                Takes priority over credentials file and JIRA_URL environment variable.
            username: JIRA username (typically an email address).
                Takes priority over credentials file and JIRA_USER environment variable.
            api_token: JIRA API token or password.
                Takes priority over credentials file and JIRA_API_TOKEN environment variable.
            credentials_file: Optional path to a JSON credentials file containing
                ``url``, ``username``, and ``api_token``.

        Returns:
            Validated JiraCredentials instance.

        Raises:
            ValueError: If any required credentials are missing or invalid.
        """
        file_values = (
            _load_credentials_file(credentials_file)
            if credentials_file is not None
            else {}
        )

        final_url = (url or file_values.get("url") or os.getenv("JIRA_URL", "")).strip()
        final_username = (
            username or file_values.get("username") or os.getenv("JIRA_USER", "")
        ).strip()
        final_token = (
            api_token or file_values.get("api_token") or os.getenv("JIRA_API_TOKEN", "")
        ).strip()

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
