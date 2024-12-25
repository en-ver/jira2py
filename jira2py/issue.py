from .jirabase import JiraBase


class Issue(JiraBase):

    def get(
        self,
        key: str,
        fields: str = "*all",
        expand: str = "names",
    ):

        kwargs = {
            "method": "GET",
            "context_path": f"issue/{key}",
            "params": {"expand": expand, "fields": fields},
        }

        issue = self._request_jira(**kwargs)
        return issue

    def get_changelogs(self, key: str, start_at: int = 0, max_results: int = 100):

        kwargs = {
            "method": "GET",
            "context_path": f"issue/{key}/changelog",
            "params": {"startAt": start_at, "maxResults": max_results},
        }

        changelogs = self._request_jira(**kwargs)
        return changelogs

    def edit(
        self,
        key: str,
        fields: dict,
        return_issue: bool = True,
        notify_users: bool = False,
        expand: str = "names",
    ):

        kwargs = {
            "method": "PUT",
            "context_path": f"issue/{key}",
            "params": {
                "notifyUsers": notify_users,
                "returnIssue": return_issue,
                "expand": expand,
            },
            "data": {"fields": fields},
        }
        response = self._request_jira(**kwargs)
        return response
