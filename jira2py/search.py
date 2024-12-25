from .jirabase import JiraBase


class Search(JiraBase):

    def jql(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int | None = 50,
        next_page_token: str | None = None,
        expand: str | None = None,
    ) -> dict:

        kwargs = {
            "method": "POST",
            "context_path": "search/jql",
            "data": {
                "jql": jql,
                "nextPageToken": next_page_token,
                "fields": fields,
                "expand": expand,
                "maxResults": max_results,
            },
        }

        return self._request_jira(**kwargs)
