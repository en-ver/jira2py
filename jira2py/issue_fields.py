from .jira_base import JiraBase
from pydantic import validate_call


class IssueFields(JiraBase):

    def _load_fields(self):

        kwargs = {"method": "GET", "context_path": "field"}
        return self._request_jira(**kwargs)

    @validate_call
    def get_fields(self) -> list[dict]:
        """
        Returns system and custom issue fields
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-fields/#api-rest-api-3-field-get

        Returns:
            list[dict]: List of issue fields
        """

        return self._load_fields()
