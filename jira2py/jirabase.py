import requests, json
from requests.auth import HTTPBasicAuth
from abc import ABC


class JiraBase(ABC):

    def _set_jira_auth(self, auth_kwargs: tuple):

        self._jira_url, self._jira_user, self._jira_api_token = auth_kwargs

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict | None = None,
        data: dict | None = None,
    ):

        try:
            response = requests.request(
                method=method,
                url=f'{self._jira_url}/rest/api/3/{context_path.strip("/")}',
                params=params,
                data=json.dumps(data) if data else None,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                auth=HTTPBasicAuth(self._jira_user, self._jira_api_token),
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise ValueError(f"HTTP error occurred: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            raise ValueError(f"Request error: {req_err}") from req_err
        except Exception as e:
            raise ValueError(f"Unexpected error: {e}") from e
