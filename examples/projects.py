import asyncio
import pprint
from typing import Any

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()


# Search projects - Sync version
def search_projects_sync(
    start_at: int = 0,
    max_results: int = 50,
) -> dict[str, Any] | None:
    """Search for projects using the sync API."""
    try:
        result = jira_sync.projects.search_projects(
            start_at=start_at,
            max_results=max_results,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects: {e}")
        return None


# Search projects - Async version
async def search_projects_async(
    start_at: int = 0,
    max_results: int = 50,
) -> dict[str, Any] | None:
    """Search for projects using the async API."""
    try:
        result = await jira_async.projects.search_projects(
            start_at=start_at,
            max_results=max_results,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects: {e}")
        return None


# Search projects by query - Sync version
def search_projects_by_query_sync(
    query: str = "service",
) -> dict[str, Any] | None:
    """Search for projects by query string using the sync API."""
    try:
        result = jira_sync.projects.search_projects(
            query=query,
            max_results=10,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects by query: {e}")
        return None


# Search projects by query - Async version
async def search_projects_by_query_async(
    query: str = "service",
) -> dict[str, Any] | None:
    """Search for projects by query string using the async API."""
    try:
        result = await jira_async.projects.search_projects(
            query=query,
            max_results=10,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects by query: {e}")
        return None


# Search projects by keys - Sync version
def search_projects_by_keys_sync(
    keys: list[str] | None = None,
) -> dict[str, Any] | None:
    """Search for projects by keys using the sync API."""
    try:
        result = jira_sync.projects.search_projects(
            keys=keys,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects by keys: {e}")
        return None


# Search projects by keys - Async version
async def search_projects_by_keys_async(
    keys: list[str] | None = None,
) -> dict[str, Any] | None:
    """Search for projects by keys using the async API."""
    try:
        result = await jira_async.projects.search_projects(
            keys=keys,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects by keys: {e}")
        return None


# Search projects with expand - Sync version
def search_projects_with_expand_sync(
    expand: list[str] | None = None,
) -> dict[str, Any] | None:
    """Search for projects with expanded properties using the sync API."""
    try:
        result = jira_sync.projects.search_projects(
            max_results=5,
            expand=expand,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects with expand: {e}")
        return None


# Search projects with expand - Async version
async def search_projects_with_expand_async(
    expand: list[str] | None = None,
) -> dict[str, Any] | None:
    """Search for projects with expanded properties using the async API."""
    try:
        result = await jira_async.projects.search_projects(
            max_results=5,
            expand=expand,
        )
        pprint.pprint(result)
        return result
    except Exception as e:
        print(f"Error searching projects with expand: {e}")
        return None


def test_sync() -> None:
    """Test sync API implementations."""
    print("=== Testing Sync API ===")

    print("Getting all projects...")
    search_projects_sync()

    # Uncomment the functions you want to test
    # print("\nSearching projects by query...")
    # search_projects_by_query_sync("service")

    # print("\nSearching projects by keys...")
    # search_projects_by_keys_sync(["PROJ", "TEST"])

    # print("\nSearching projects with expand...")
    # search_projects_with_expand_sync(["description", "lead", "issueTypes"])


def test_sync_with_context_manager() -> None:
    """Test sync API with auto-managed persistent clients."""
    print("=== Testing Sync API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPI()
    print("Getting all projects with auto-managed clients...")
    try:
        result = api.projects.search_projects()
        pprint.pprint(result)
    except Exception as e:
        print(f"Error searching projects: {e}")

    print("\nSearching projects by query with auto-managed clients...")
    try:
        result = api.projects.search_projects(query="service", max_results=10)
        pprint.pprint(result)
    except Exception as e:
        print(f"Error searching projects by query: {e}")

    print("Auto-managed clients handle resource cleanup automatically")


async def test_async() -> None:
    """Test async API implementations."""
    print("=== Testing Async API ===")

    print("Getting all projects...")
    await search_projects_async()

    # Uncomment the functions you want to test
    # print("\nSearching projects by query...")
    # await search_projects_by_query_async("service")

    # print("\nSearching projects by keys...")
    # await search_projects_by_keys_async(["PROJ", "TEST"])

    # print("\nSearching projects with expand...")
    # await search_projects_with_expand_async(["description", "lead", "issueTypes"])


async def test_async_with_context_manager() -> None:
    """Test async API with auto-managed persistent clients."""
    print("=== Testing Async API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPIAsync()
    print("Getting all projects with auto-managed async clients...")
    try:
        result = await api.projects.search_projects()
        pprint.pprint(result)
    except Exception as e:
        print(f"Error searching projects: {e}")

    print("\nSearching projects by query with auto-managed async clients...")
    try:
        result = await api.projects.search_projects(query="service", max_results=10)
        pprint.pprint(result)
    except Exception as e:
        print(f"Error searching projects by query: {e}")

    print("Auto-managed async clients handle resource cleanup automatically")


def main() -> None:
    """Run both sync and async tests."""
    print("Starting Jira2py Projects API Tests...")
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
