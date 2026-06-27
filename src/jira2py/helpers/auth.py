"""Grouped authentication helper operations for jira2py."""

from __future__ import annotations

from typing import Any

from jira2py.api import JiraAPI

from .errors import JiraHelperOperationError
from .models import JiraUser
from .results import HelperResult


class AuthHelpers:
    """High-level grouped helpers for Jira authentication/status operations."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api

    def me(self) -> HelperResult:
        """Get the currently authenticated Jira user."""
        try:
            data = self.api.users.get_current_user()
        except Exception as exc:
            raise JiraHelperOperationError(
                f"Failed to fetch current user: {exc}"
            ) from exc

        user = JiraUser.model_validate(data)
        return HelperResult.with_data(self._format_me_text(user, data), data)

    def status(self) -> HelperResult:
        """Probe Jira authentication status via the current-user endpoint."""
        try:
            data = self.api.users.get_current_user()
        except Exception as exc:
            status_data: dict[str, Any] = {
                "ok": False,
                "authenticated": False,
                "url": self.api.credentials.url,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
            status_code = getattr(exc, "status_code", None)
            if isinstance(status_code, int):
                status_data["status_code"] = status_code
            return HelperResult.with_data(
                f"Authentication failed for {self.api.credentials.url}: {exc}",
                status_data,
            )

        user = JiraUser.model_validate(data)
        return HelperResult.with_data(
            (
                f"Authentication OK for {self.api.credentials.url}\n"
                f"User: {user.displayName} ({user.accountId})"
            ),
            {
                "ok": True,
                "authenticated": True,
                "url": self.api.credentials.url,
                "user": data,
            },
        )

    @staticmethod
    def _format_me_text(user: JiraUser, data: dict[str, Any]) -> str:
        lines = [
            "Authenticated Jira user",
            f"Display Name: {user.displayName}",
            f"Account ID: {user.accountId}",
            f"Active: {'yes' if user.active else 'no'}",
        ]
        email = data.get("emailAddress")
        if isinstance(email, str) and email:
            lines.append(f"Email: {email}")
        account_type = data.get("accountType")
        if isinstance(account_type, str) and account_type:
            lines.append(f"Account Type: {account_type}")
        return "\n".join(lines)


__all__ = ["AuthHelpers"]
