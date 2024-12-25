from requests.auth import HTTPBasicAuth
import json, os, requests
from decimal import Decimal
from abc import ABC


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class JiraBase(ABC):

    def _request_jira(
        self,
        method: str,
        context_path: str,
        params: dict | None = None,
        data: dict | None = None,
    ) -> any:

        jira_url = os.getenv("_JIRA_URL", None)
        jira_user = os.getenv("_JIRA_USER", None)
        jira_api_token = os.getenv("_JIRA_API_TOKEN", None)

        try:
            response = requests.request(
                method=method,
                url=f'{jira_url}/rest/api/3/{context_path.strip("/")}',
                params=params,
                data=json.dumps(data, cls=DecimalEncoder) if data else None,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                auth=HTTPBasicAuth(jira_user, jira_api_token),
            )
            return response.json()
        except Exception as e:
            raise e
