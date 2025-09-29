import asyncio
import pprint
from typing import Any

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()


# Get all Jira fields with its metadata - Sync version
def get_all_fields_sync() -> list[dict[str, Any]] | None:
    """Get all Jira fields using the sync API."""
    try:
        jira_fields = jira_sync.fields.get_fields()
        pprint.pprint(jira_fields)
        return jira_fields
    except Exception as e:
        print(f"Error getting Jira fields: {e}")
        return None


# Get all Jira fields with its metadata - Async version
async def get_all_fields_async() -> list[dict[str, Any]] | None:
    """Get all Jira fields using the async API."""
    try:
        jira_fields = await jira_async.fields.get_fields()
        pprint.pprint(jira_fields)
        return jira_fields
    except Exception as e:
        print(f"Error getting Jira fields: {e}")
        return None


def test_sync() -> None:
    """Test sync API implementations."""
    print("=== Testing Sync API ===")
    print("Getting all fields...")
    get_all_fields_sync()


def test_sync_with_context_manager() -> None:
    """Test sync API with auto-managed persistent clients."""
    print("=== Testing Sync API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPI()
    print("Getting all fields with auto-managed clients...")
    try:
        jira_fields = api.fields.get_fields()
        pprint.pprint(jira_fields)
    except Exception as e:
        print(f"Error getting Jira fields: {e}")

    print("Auto-managed clients handle resource cleanup automatically")


async def test_async() -> None:
    """Test async API implementations."""
    print("=== Testing Async API ===")
    print("Getting all fields...")
    await get_all_fields_async()


async def test_async_with_context_manager() -> None:
    """Test async API with auto-managed persistent clients."""
    print("=== Testing Async API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPIAsync()
    print("Getting all fields with auto-managed async clients...")
    try:
        jira_fields = await api.fields.get_fields()
        pprint.pprint(jira_fields)
    except Exception as e:
        print(f"Error getting Jira fields: {e}")

    print("Auto-managed async clients handle resource cleanup automatically")


def main() -> None:
    """Run both sync and async tests."""
    print("Starting Jira2py Issue Fields API Tests...")
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
