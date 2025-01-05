from pydantic import validate_call, EmailStr, HttpUrl

"""
This module provides the main `Jira` class for interacting with a Jira instance.

The `Jira` class serves as an entry point to various functionalities such as working with issues, 
executing JQL queries, and accessing Jira fields. Initialize the `Jira` class with the 
necessary credentials to begin using its features.
"""


class Jira:
    """
    A client for interacting with a Jira instance.

    This class provides methods for managing Jira issues, executing JQL queries,
    and retrieving metadata about fields. It simplifies authentication and
    interaction with Jira's APIs by centralizing the required credentials.

    Initialize this class with your Jira instance's URL, user email, and API token.
    """

    @validate_call
    def __init__(
        self,
        jira_url: HttpUrl,
        jira_user: EmailStr,
        jira_api_token: str,
    ):
        """
        Set up the Jira client with authentication details.

        Use this method to configure the Jira client by providing the base URL
        of your Jira instance, your user email, and your API token.

        Args:
            jira_url (str): The base URL of the Jira instance (e.g., https://yourcompany.atlassian.net).
            jira_user (str): The email address associated with your Jira account.
            jira_api_token (str): The API token used for authenticating with Jira.
        """

        self._auth_kwargs = (jira_url, jira_user, jira_api_token)

    @validate_call
    def issue(self, id_key: str | None = None):
        """
        Retrieve or initialize a Jira issue.

        This method provides access to Jira issues. By providing an issue key
        or ID, you can interact with a specific Jira issue. If no key is
        provided, you can initialize the issue object for further configuration.

        Args:
            id_key (str | None): The unique key or ID of the Jira issue. If None,
                                 the method initializes the issue object without
                                 targeting a specific issue.

        Returns:
            Issue: An object for managing the specified Jira issue or initializing a new one.
        """
        from .issue import Issue

        return Issue(auth_kwargs=self._auth_kwargs, key_id=id_key)

    @validate_call
    def jql(self, jql: str):
        """
        Execute a JQL query to retrieve issues.

        Use this method to search for Jira issues that match a given JQL (Jira Query Language)
        expression. It returns a JQL object for handling the results.

        Args:
            jql (str): A valid JQL query string.

        Returns:
            JQL: An object for managing the query and its results.
        """
        from .jql import JQL

        return JQL(auth_kwargs=self._auth_kwargs, jql=jql)

    @validate_call
    def fields(self):
        """
        Retrieve metadata about Jira fields.

        This method provides access to Jira fields, including information about
        custom fields. Use it to retrieve a comprehensive list of fields available
        in your Jira instance.

        Returns:
            Fields: An object for managing field-related data.
        """
        from .fields import Fields

        return Fields(auth_kwargs=self._auth_kwargs)
