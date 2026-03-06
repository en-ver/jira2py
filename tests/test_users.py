"""Tests for Users API."""

import httpx

from jira2py.api.users import Users

SAMPLE_USERS = [
    {"accountId": "user1", "displayName": "John Doe", "active": True},
    {"accountId": "user2", "displayName": "Jane Smith", "active": True},
]


class TestUsers:
    """Tests for Users API."""

    def test_search_users(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_USERS)

        api = Users(make_client(handler))
        result = api.search_users("john")

        assert len(result) == 2
        assert result[0]["displayName"] == "John Doe"

    def test_search_users_with_pagination(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=SAMPLE_USERS)

        api = Users(make_client(handler))
        result = api.search_users("john", start_at=10, max_results=25)

        assert len(result) == 2
