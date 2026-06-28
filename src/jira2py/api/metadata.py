"""Metadata API implementation."""

from collections.abc import Mapping
from typing import Any

from .api_base import ApiBase


class Metadata(ApiBase):
    """Metadata API — shared Jira Cloud metadata resources."""

    def get_statuses(
        self,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get Jira statuses visible to the current user.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-workflow-statuses/#api-rest-api-3-status-get
        """
        return self._as_list(
            self._client._request_jira(
                method="GET",
                context_path="status",
                extra_params=extra_params,
            )
        )

    def get_priorities(
        self,
        extra_params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Get Jira priorities visible to the current user.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-priorities/#api-rest-api-3-priority-get
        """
        return self._as_list(
            self._client._request_jira(
                method="GET",
                context_path="priority",
                extra_params=extra_params,
            )
        )
