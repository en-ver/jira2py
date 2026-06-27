"""Tests for Users API."""

import httpx
import pytest

from jira2py import JiraAPI
from jira2py.api.users import Users

SAMPLE_USERS = [
    {"accountId": "user1", "displayName": "John Doe", "active": True},
    {"accountId": "user2", "displayName": "Jane Smith", "active": True},
]

SAMPLE_CURRENT_USER = {
    "accountId": "current-user",
    "displayName": "Current User",
    "active": True,
    "emailAddress": "current@example.com",
}


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

    def test_get_current_user_returns_raw_response_and_path(self, make_client):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/rest/api/3/myself"
            return httpx.Response(200, json=SAMPLE_CURRENT_USER)

        api = Users(make_client(handler))
        result = api.get_current_user()

        assert result == SAMPLE_CURRENT_USER

    def test_get_current_user_raises_type_error_for_non_dict_response(
        self, make_client
    ):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[SAMPLE_CURRENT_USER])

        api = Users(make_client(handler))

        with pytest.raises(TypeError, match="Expected dict response"):
            api.get_current_user()


class TestJiraAPIUsersFacade:
    """Tests for JiraAPI users facade."""

    def test_users_property_is_cached(self):
        jira = JiraAPI(
            url="https://test.atlassian.net",
            username="test@example.com",
            api_token="test-token",
        )

        first = jira.users
        second = jira.users

        assert isinstance(first, Users)
        assert first is second
