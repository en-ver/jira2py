from .jirabase import JiraBase


class Fields(JiraBase):

    def get(self) -> list[dict]:

        kwargs = {"method": "GET", "context_path": "field"}

        return self._request_jira(**kwargs)
