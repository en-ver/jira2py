from .jirabase import JiraBase
from pydantic import validate_call


class JQL(JiraBase):

    @validate_call
    def __init__(
        self,
        auth_kwargs: tuple,
        jql: str,
    ):

        self._set_jira_auth(auth_kwargs)
        self.jql = jql

    def _jql_page_loader(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int | None = 100,
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

    @validate_call
    def get_page(
        self,
        fields: list[str] | None = ["*all"],
        max_results: int | None = 100,
        next_page_token: str | None = None,
        expand: str | None = "names",
    ) -> dict:
        """
        Retrieve a single page of issues matching the JQL query.

        This method fetches a single page of issues that match the JQL query associated with
        this object. You can customize the response by specifying fields to include,
        pagination options, and additional properties to expand.

        Args:
            fields (list[str] | None): Optional. A list of field names to include in the
                                       response. Defaults to all fields (`"*all"`).
            max_results (int | None): Optional. The maximum number of issues to return in
                                      the response. Defaults to 100.
            next_page_token (str | None): Optional. A token indicating where to start the
                                          next page of results. Defaults to None.
            expand (str | None): Optional. Additional properties to include in the
                                 response (e.g., "names"). Defaults to "names".

        Returns:
            dict: A dictionary containing the issues in the current page and other metadata.
        """

        return self._jql_page_loader(
            jql=self.jql,
            fields=fields,
            max_results=max_results,
            next_page_token=next_page_token,
            expand=expand,
        )

    @validate_call
    def get_all_pages(
        self,
        fields: list[str] | None = ["*all"],
        expand: str | None = "names",
    ) -> list[dict]:
        """
        Retrieve all issues matching the JQL query across all pages.

        This method iteratively fetches all issues that match the JQL query associated
        with this object, handling pagination automatically. You can customize the response
        by specifying fields to include and additional properties to expand.

        Args:
            fields (list[str] | None): Optional. A list of field names to include in the
                                       response. Defaults to all fields (`"*all"`).
            expand (str | None): Optional. Additional properties to include in the
                                 response (e.g., "names"). Defaults to "names".

        Returns:
            list: A list of dictionaries containing all issues that match the JQL query.
        """

        all_issues = {}
        is_last = False
        next_page_token = None

        while not is_last:

            search_result_json = self._jql_page_loader(
                jql=self.jql,
                fields=fields,
                next_page_token=next_page_token,
                expand=expand,
            )

            all_issues.setdefault("issues", []).extend(
                search_result_json.get("issues", [])
            )

            if "names" in expand and not "names" in all_issues:
                all_issues.update({"names": search_result_json.get("names", {})})

            next_page_token = search_result_json.get("nextPageToken", None)
            is_last = False if next_page_token else True

        return all_issues
