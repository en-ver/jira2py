import asyncio
import pprint
from typing import Any

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()

# Change the JQL query to the one you want to test
jql = "project IN (PR)"


# Search for issues using JQL - Sync version
def enhanced_search_sync(query: str = jql) -> dict[str, Any] | None:
    """Search for issues using JQL with the sync API."""
    try:
        search_results = jira_sync.search.enhanced_search(jql=query, fields=["summary"])
        pprint.pprint(search_results)
        return search_results
    except Exception as e:
        print(f"Error searching issues with query '{query}': {e}")
        return None


# Search for issues using JQL - Async version
async def enhanced_search_async(query: str = jql) -> dict[str, Any] | None:
    """Search for issues using JQL with the async API."""
    try:
        search_results = await jira_async.search.enhanced_search(
            jql=query, fields=["summary"]
        )
        pprint.pprint(search_results)
        return search_results
    except Exception as e:
        print(f"Error searching issues with query '{query}': {e}")
        return None


def enhanced_search_with_extra_params_sync(query: str = jql) -> dict[str, Any] | None:
    """Search for issues using JQL with additional parameters - Sync version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params: dict[str, Any] = {"startAt": 0, "maxResults": 10}

        # Example of using extra_data to add additional data parameters
        extra_data: dict[str, Any] = {
            "fieldsByKeys": True,
            "expand": "changelog,renderedFields",
        }

        search_results = jira_sync.search.enhanced_search(
            jql=query,
            fields=["summary", "status"],
            extra_params=extra_params,
            extra_data=extra_data,
        )
        pprint.pprint(search_results)
        return search_results
    except Exception as e:
        print(f"Error searching issues with extra params '{query}': {e}")
        return None


async def enhanced_search_with_extra_params_async(
    query: str = jql,
) -> dict[str, Any] | None:
    """Search for issues using JQL with additional parameters - Async version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params: dict[str, Any] = {"startAt": 0, "maxResults": 10}

        # Example of using extra_data to add additional data parameters
        extra_data: dict[str, Any] = {
            "fieldsByKeys": True,
            "expand": "changelog,renderedFields",
        }

        search_results = await jira_async.search.enhanced_search(
            jql=query,
            fields=["summary", "status"],
            extra_params=extra_params,
            extra_data=extra_data,
        )
        pprint.pprint(search_results)
        return search_results
    except Exception as e:
        print(f"Error searching issues with extra params '{query}': {e}")
        return None


def test_sync() -> None:
    """Test sync API implementations."""
    print("=== Testing Sync API ===")
    print("Performing enhanced search...")
    enhanced_search_sync()

    print("\nPerforming enhanced search with extra params...")
    enhanced_search_with_extra_params_sync()


def test_sync_with_context_manager() -> None:
    """Test sync API with auto-managed persistent clients."""
    print("=== Testing Sync API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPI()
    print("Performing enhanced search with auto-managed clients...")
    try:
        search_results = api.search.enhanced_search(jql=jql, fields=["summary"])
        pprint.pprint(search_results)
    except Exception as e:
        print(f"Error searching issues with query '{jql}': {e}")

    print("\nPerforming enhanced search with extra params...")
    try:
        extra_params: dict[str, Any] = {"startAt": 0, "maxResults": 10}
        extra_data: dict[str, Any] = {
            "fieldsByKeys": True,
            "expand": "changelog,renderedFields",
        }

        search_results = api.search.enhanced_search(
            jql=jql,
            fields=["summary", "status"],
            extra_params=extra_params,
            extra_data=extra_data,
        )
        pprint.pprint(search_results)
    except Exception as e:
        print(f"Error searching issues with extra params '{jql}': {e}")

    print("Auto-managed clients handle resource cleanup automatically")


async def test_async() -> None:
    """Test async API implementations."""
    print("=== Testing Async API ===")
    print("Performing enhanced search...")
    await enhanced_search_async()

    print("\nPerforming enhanced search with extra params...")
    await enhanced_search_with_extra_params_async()


async def test_async_with_context_manager() -> None:
    """Test async API with auto-managed persistent clients."""
    print("=== Testing Async API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPIAsync()
    print("Performing enhanced search with auto-managed async clients...")
    try:
        search_results = await api.search.enhanced_search(jql=jql, fields=["summary"])
        pprint.pprint(search_results)
    except Exception as e:
        print(f"Error searching issues with query '{jql}': {e}")

    print("\nPerforming enhanced search with extra params...")
    try:
        extra_params: dict[str, Any] = {"startAt": 0, "maxResults": 10}
        extra_data: dict[str, Any] = {
            "fieldsByKeys": True,
            "expand": "changelog,renderedFields",
        }

        search_results = await api.search.enhanced_search(
            jql=jql,
            fields=["summary", "status"],
            extra_params=extra_params,
            extra_data=extra_data,
        )
        pprint.pprint(search_results)
    except Exception as e:
        print(f"Error searching issues with extra params '{jql}': {e}")

    print("Auto-managed async clients handle resource cleanup automatically")


def main() -> None:
    """Run both sync and async tests."""
    print("Starting Jira2py Issue Search API Tests...")
    print("=" * 50)

    # Test sync API
    test_sync()

    print("\n" + "=" * 50)

    # Test sync API with context manager (recommended approach)
    test_sync_with_context_manager()

    print("\n" + "=" * 50)

    # Test async API
    asyncio.run(test_async())

    print("\n" + "=" * 50)

    # Test async API with context manager (recommended approach)
    asyncio.run(test_async_with_context_manager())

    print("\n" + "=" * 50)
    print("All tests completed!")
    print("\nNote: The context manager examples demonstrate the recommended approach")
    print("for proper resource management with the client injection pattern.")


if __name__ == "__main__":
    main()
