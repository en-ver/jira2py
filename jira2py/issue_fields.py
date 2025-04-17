from .jirabase import JiraBase
from pydantic import validate_call


class IssueFields(JiraBase):

    def __init__(self, auth_kwargs: tuple):

        self._set_jira_auth(auth_kwargs)

    def _load_fields(self):

        kwargs = {"method": "GET", "context_path": "field"}
        return self._request_jira(**kwargs)

    def get_fields(self):
        return self._load_fields()
