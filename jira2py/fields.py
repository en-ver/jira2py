from .jirabase import JiraBase
from pydantic import validate_call
from warnings import deprecated


class Fields(JiraBase):

    def __init__(self, auth_kwargs: tuple):

        self._set_jira_auth(auth_kwargs)

    def _load_fields(self):

        kwargs = {"method": "GET", "context_path": "field"}
        return self._request_jira(**kwargs)

    @deprecated("The method is not maintained starting from 1.0.0")
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

    @deprecated(
        "The method is not maintained starting from 1.0.0. Use `get_fields()` instead."
    )
    def get(self) -> list[dict]:
        return self._load_fields()

    @deprecated("The method is not maintained starting from 1.0.0")
    def get_field_id(self, field_names: list[str]) -> list[str]:
        return self._get_field_attr(
            in_attr_name="name", in_attr_values=field_names, out_attr_name="id"
        )

    @deprecated("The method is not maintained starting from 1.0.0")
    def get_field_name(self, field_ids: list[str]) -> list[str]:
        return self._get_field_attr(
            in_attr_name="id", in_attr_values=field_ids, out_attr_name="name"
        )

    def get_fields(self):

        return self._load_fields()
