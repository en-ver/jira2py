from typing import Any, cast

from pydantic import validate_call

from jira2py.client import JiraClientSync
from jira2py.client import JiraCredentials


class IssueFields(JiraClientSync):
    """A class to interact with Jira's issue fields API."""

    def __init__(self, credentials: JiraCredentials | None = None):
        """Initialize the IssueFields client.

        Args:
            credentials: JIRA authentication credentials. If None, loads from environment.
        """
        super().__init__(credentials)

    @validate_call
    def get_fields(self) -> list[dict[str, Any]]:
        """Returns system and custom issue fields
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            list[dict]: List of issue fields
        """

        return cast(
            list[dict[str, Any]],
            self._request_jira(
                method="GET",
                context_path="field",
                response_type="list",
            ),
        )
