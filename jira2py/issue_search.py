from .jira_base import JiraBase
from pydantic import validate_call


class IssueSearch(JiraBase):

    @validate_call
    def enhanced_search(
        self,
        jql: str,
        next_page_token: str | None = None,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: str | None = None,
        properties: list[str] | None = None,
        fields_by_keys: bool = False,
        fail_fast: bool = False,
        reconcile_issues: list[int] | None = [],
    ) -> dict:
        """Searches for issues using JQL.
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post

        Args:
            jql (str): The JQL query string to search for issues.
            next_page_token (str, optional): A token to fetch the next page of results.
            max_results (int, optional): The maximum number of items to return per page. Defaults to 50.
            fields (list[str], optional): A list of fields to return for each issue. Use "*all" for all fields.
            expand (str, optional): A comma-separated list of properties to expand.
            properties (list[str], optional): A list of properties to include in the response.
            fields_by_keys (bool, optional): Whether to reference fields by their keys instead of IDs. Defaults to False.
            fail_fast (bool, optional): Whether to fail fast if the JQL query is invalid. Defaults to False.
            reconcile_issues (list[int], optional): A list of issue keys to ensure read-after-write consistency.

        Returns:
            dict: A dictionary containing the search results, including issues and metadata.
        """

        kwargs = {
            "method": "POST",
            "context_path": "search/jql",
            "data": {
                "jql": jql,
                "nextPageToken": next_page_token,
                "maxResults": max_results,
                "fields": fields,
                "expand": expand,
                "properties": properties,
                "fieldsByKeys": fields_by_keys,
                "failFast": fail_fast,
                "reconcileIssues": reconcile_issues,
            },
        }

        return self._request_jira(**kwargs)
