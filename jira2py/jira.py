from requests.auth import HTTPBasicAuth
import json, os
from decimal import Decimal


class Jira:

    def __init__(self, url: str, user: str, api_token: str):

        os.environ["_JIRA_URL"] = url
        os.environ["_JIRA_USER"] = user
        os.environ["_JIRA_API_TOKEN"] = api_token

    def search(self):
        from .search import Search

        return Search()

    def issue(self):
        from .issue import Issue

        return Issue()

    def fields(self):
        from .fields import Fields

        return Fields()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)
