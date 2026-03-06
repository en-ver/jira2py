"""Issue Fields API implementation."""

from typing import Any

from .api_base import ApiBase


class IssueFields(ApiBase):
    """Issue Fields API — list system and custom fields."""

    def get_fields(self) -> list[dict[str, Any]]:
        """Get all system and custom issue fields.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            List of field objects with id, name, custom, schema, etc.
        """
        return self._as_list(
            self._client._request_jira(
                method="GET",
                context_path="field",
            )
        )
