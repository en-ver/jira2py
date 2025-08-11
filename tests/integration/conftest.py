"""Shared fixtures for integration tests."""

import os
from typing import Optional

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def jira_url() -> Optional[str]:
    """Returns the Jira URL from environment variables."""
    return os.getenv("JIRA_URL")


@pytest.fixture(scope="session")
def jira_user() -> Optional[str]:
    """Returns the Jira user from environment variables."""
    return os.getenv("JIRA_USER")


@pytest.fixture(scope="session")
def jira_api_token() -> Optional[str]:
    """Returns the Jira API token from environment variables."""
    return os.getenv("JIRA_API_TOKEN")


@pytest.fixture(scope="session")
def has_integration_config(
    jira_url: Optional[str], jira_user: Optional[str], jira_api_token: Optional[str]
) -> bool:
    """Check if all required integration test configuration is available."""
    return all([jira_url, jira_user, jira_api_token])
