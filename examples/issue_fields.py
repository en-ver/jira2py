import asyncio
import pprint

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()


# Get all Jira fields with its metadata - Sync version
def get_all_fields_sync() -> list | None:
    """Get all Jira fields using the sync API."""
    try:
        jira_fields = jira_sync.fields.get_fields()
        pprint.pprint(jira_fields)
        return jira_fields
    except Exception as e:
        print(f"Error getting Jira fields: {e}")
        return None


# Get all Jira fields with its metadata - Async version
async def get_all_fields_async() -> list | None:
    """Get all Jira fields using the async API."""
    try:
        jira_fields = await jira_async.fields.get_fields()
        pprint.pprint(jira_fields)
        return jira_fields
    except Exception as e:
        print(f"Error getting Jira fields: {e}")
        return None


def test_sync():
    """Test sync API implementations."""
    print("=== Testing Sync API ===")
    print("Getting all fields...")
    get_all_fields_sync()


async def test_async():
    """Test async API implementations."""
    print("=== Testing Async API ===")
    print("Getting all fields...")
    await get_all_fields_async()


def main():
    """Run both sync and async tests."""
    print("Starting Jira2py Issue Fields API Tests...")
    print("=" * 50)

    # Test sync API
    test_sync()

    print("\n" + "=" * 50)

    # Test async API
    asyncio.run(test_async())

    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()
