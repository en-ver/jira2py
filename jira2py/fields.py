from .jira_base import JiraBase
from pydantic import validate_call

"""
This module provides the `Fields` class, which allows interaction with Jira field metadata.

The `Fields` class enables users to retrieve and manage information about fields available in a Jira instance. 
It includes methods for listing all fields, retrieving field IDs based on field names, and retrieving field 
names based on field IDs. 

This functionality simplifies working with Jira's field data for custom integrations and automation.
"""


class Fields(JiraBase):

    def __init__(self, auth_kwargs: tuple):

        self._set_jira_auth(auth_kwargs)

    def _load_fields(self):

        kwargs = {"method": "GET", "context_path": "field"}
        return self._request_jira(**kwargs)

    def _get_field_attr(
        self,
        in_attr_name: str,
        in_attr_values: str | list[str],
        out_attr_name: str | list[str],
    ):

        fields = self._load_fields()

        return [
            field.get(out_attr_name, None)
            for attr_value in in_attr_values
            for field in fields
            if field.get(in_attr_name, None) == attr_value
        ]

    def get(self) -> list[dict]:
        """
        Retrieve all available fields in the Jira instance.

        This method fetches a list of all fields currently available in the Jira instance,
        including standard and custom fields. It provides comprehensive metadata for each
        field, which can be used for various integrations and automations.

        Returns:
            list[dict]: A list of dictionaries where each dictionary contains metadata
                        about a field (e.g., field ID, name, and other attributes).
        """

        return self._load_fields()

    @validate_call
    def get_field_id(self, field_names: list[str]) -> list[str]:
        """
        Retrieve the IDs of fields based on their names.

        This method takes a list of field names and returns a list of corresponding field IDs
        available in the Jira instance.

        Args:
            field_names (list[str]): A list of field names to search for.

        Returns:
            list[str]: A list of field IDs that correspond to the provided field names.
        """

        return self._get_field_attr(
            in_attr_name="name", in_attr_values=field_names, out_attr_name="id"
        )

    @validate_call
    def get_field_name(self, field_ids: list[str]) -> list[str]:
        """
        Retrieve the names of fields based on their IDs.

        This method takes a list of field IDs and returns a list of corresponding field names
        available in the Jira instance.

        Args:
            field_ids (list[str]): A list of field IDs to search for.

        Returns:
            list[str]: A list of field names that correspond to the provided field IDs.
        """

        return self._get_field_attr(
            in_attr_name="id", in_attr_values=field_ids, out_attr_name="name"
        )
