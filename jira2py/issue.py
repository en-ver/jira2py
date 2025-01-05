from .jirabase import JiraBase
from pydantic import validate_call


class Issue(JiraBase):

    @validate_call
    def __init__(
        self,
        auth_kwargs: tuple,
        key_id: str | int | None = None,
    ):

        self._set_jira_auth(auth_kwargs)
        self.key_id = key_id

    @validate_call
    def get(
        self, fields: list[str] | None = ["*all"], expand: str | None = "names"
    ) -> dict:
        """
        Retrieve details of the associated Jira issue.

        This method fetches the details of the Jira issue specified by `key_id` with
        options to customize the fields and expand properties in the response.

        Args:
            fields (list[str] | None): Optional. A list of field names to include in
                                       the response. Defaults to all fields (`"*all"`).
            expand (str | None): Optional. Specifies additional information to include
                                 in the response (e.g., "names"). Defaults to "names".

        Returns:
            dict: A dictionary containing the issue details.
        """

        kwargs = {
            "method": "GET",
            "context_path": f"issue/{self.key_id}",
            "params": {"expand": expand, "fields": ",".join(fields)},
        }

        issue = self._request_jira(**kwargs)
        return issue

    def _changelog_page_loader(
        self,
        start_at: int | None = None,
        max_results: int | None = None,
        fields: list[str] | None = None,
    ) -> dict:

        kwargs = {
            "method": "GET",
            "context_path": f"issue/{self.key_id}/changelog",
            "params": {"startAt": start_at, "maxResults": max_results},
        }

        changelogs = self._request_jira(**kwargs)

        if fields:

            fields_set = set(fields)

            def filter_items(items: list | None = []):
                """Filter items based on fieldId matching field IDs."""
                return [item for item in items if item.get("fieldId", "") in fields_set]

            filtered_values = [
                {
                    **value,
                    "items": filter_items(value.get("items", [])),
                }
                for value in changelogs.get("values", [])
                if filter_items(value.get("items", []))
            ]

            changelogs.update({"values": filtered_values})

        return changelogs

    @validate_call
    def changelog_page(
        self,
        start_at: int | None = None,
        max_results: int | None = None,
        fields: list[str] | None = None,
    ) -> dict:
        """
        Retrieve a single page of changelog entries for the issue.

        This method fetches one page of changelog data for the associated Jira issue,
        optionally filtered by specific field IDs.

        Args:
            start_at (int | None): Optional. The starting index for pagination. Defaults to None.
            max_results (int | None): Optional. The maximum number of results to return. Defaults to None.
            fields (list[str] | None): Optional. A list of field IDs to filter changelog entries.
                                       Defaults to None.

        Returns:
            dict: A dictionary containing the changelog data for the requested page.
        """

        return self._changelog_page_loader(
            start_at=start_at, max_results=max_results, fields=fields
        )

    @validate_call
    def changelog_all_pages(self, fields: list[str] | None = None) -> list[dict]:
        """
        Retrieve all changelog entries for the issue.

        This method fetches all pages of changelog data for the associated Jira issue
        by iterating through paginated results. Optionally, changelog entries can be
        filtered by specific field IDs.

        Args:
            fields (list[str] | None): Optional. A list of field IDs to filter changelog entries.
                                       Defaults to None.

        Returns:
            list[dict]: A list of dictionaries containing all changelog entries for the issue.
        """

        start_at = 0
        changelog = []

        while True:

            response = self.changelog_page(start_at=start_at, fields=fields)
            start_at += response.get("maxResults", 0)
            changelog.extend(response.get("values", []))
            if response.get("isLast", True):
                break

        return changelog

    @validate_call
    def edit(
        self,
        fields: dict,
        return_issue: bool | None = True,
        notify_users: bool | None = False,
        expand: str | None = "names",
    ) -> dict:
        """
        Edit the details of the associated Jira issue.

        This method updates the specified fields of the Jira issue and provides options
        to notify users, return the updated issue, and include expanded properties.

        Args:
            fields (dict): A dictionary of field names and their new values to update the issue.
            return_issue (bool | None): Optional. Whether to return the updated issue details.
                                        Defaults to True.
            notify_users (bool | None): Optional. Whether to notify users about the update.
                                        Defaults to False.
            expand (str | None): Optional. Specifies additional information to include
                                 in the response. Defaults to "names".

        Returns:
            dict: A dictionary containing the server's response to the update request.
        """

        kwargs = {
            "method": "PUT",
            "context_path": f"issue/{self.key_id}",
            "params": {
                "notifyUsers": notify_users,
                "returnIssue": return_issue,
                "expand": expand,
            },
            "data": {"fields": fields},
        }
        response = self._request_jira(**kwargs)
        return response
