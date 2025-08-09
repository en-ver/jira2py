from pydantic import validate_call

from .jira_base import JiraBase


class IssueFields(JiraBase):
    """A class to interact with Jira's issue fields API."""

    @validate_call
    def get_fields(self) -> list[dict]:
        """Returns system and custom issue fields
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            list[dict]: List of issue fields
        """

        kwargs = {
            "method": "GET",
            "context_path": "field",
            "params": None,
            "data": None,
        }

        return self._request_jira(**kwargs)
