from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock

import pytest

from jira2py import JiraAPI
from jira2py.exceptions import JiraAuthenticationError
from jira2py.helpers.auth import AuthHelpers
from jira2py.helpers.errors import JiraHelperOperationError


def _make_api() -> SimpleNamespace:
    return SimpleNamespace(
        credentials=SimpleNamespace(url="https://example.atlassian.net"),
        users=Mock(),
    )


def test_me_formats_current_user_details() -> None:
    api = _make_api()
    api.users.get_current_user.return_value = {
        "accountId": "acct-1",
        "displayName": "Alice Example",
        "active": True,
        "emailAddress": "alice@example.com",
        "accountType": "atlassian",
    }

    result = AuthHelpers(cast(JiraAPI, api)).me()

    api.users.get_current_user.assert_called_once_with()
    assert result.data == api.users.get_current_user.return_value
    assert result.text == (
        "Authenticated Jira user\n"
        "Display Name: Alice Example\n"
        "Account ID: acct-1\n"
        "Active: yes\n"
        "Email: alice@example.com\n"
        "Account Type: atlassian"
    )


def test_me_wraps_failures() -> None:
    api = _make_api()
    api.users.get_current_user.side_effect = RuntimeError("boom")

    with pytest.raises(JiraHelperOperationError, match="Failed to fetch current user"):
        AuthHelpers(cast(JiraAPI, api)).me()


def test_status_reports_authenticated_user() -> None:
    api = _make_api()
    api.users.get_current_user.return_value = {
        "accountId": "acct-1",
        "displayName": "Alice Example",
        "active": True,
    }

    result = AuthHelpers(cast(JiraAPI, api)).status()

    assert result.text == (
        "Authentication OK for https://example.atlassian.net\n"
        "User: Alice Example (acct-1)"
    )
    assert result.data == {
        "ok": True,
        "authenticated": True,
        "url": "https://example.atlassian.net",
        "user": api.users.get_current_user.return_value,
    }


def test_status_returns_agent_readable_failure_result() -> None:
    api = _make_api()
    api.users.get_current_user.side_effect = JiraAuthenticationError(
        "Bad credentials",
        status_code=401,
        response=None,
    )

    result = AuthHelpers(cast(JiraAPI, api)).status()

    assert result.text == (
        "Authentication failed for https://example.atlassian.net: Bad credentials"
    )
    assert result.data == {
        "ok": False,
        "authenticated": False,
        "url": "https://example.atlassian.net",
        "error": "Bad credentials",
        "error_type": "JiraAuthenticationError",
        "status_code": 401,
    }
