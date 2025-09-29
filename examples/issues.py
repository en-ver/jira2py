import asyncio
import pprint

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()

# Or provide credentials directly:
# jira_sync = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
# jira_async = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")

# Or provide credentials directly:
# jira_sync = JiraAPI(url="https://company.atlassian.net", username="user@example.com", api_token="token")
# jira_async = JiraAPIAsync(url="https://company.atlassian.net", username="user@example.com", api_token="token")

# Change the issue ID to the one you want to test
issue_id = "PR-24446"


# Get an issue by its ID - Sync version
def get_issue_sync(issue_key: str = issue_id) -> dict[str, object] | None:
    """Get an issue by its ID using the sync API."""
    try:
        issue = jira_sync.issues.get_issue(issue_key)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue {issue_key}: {e}")
        return None


# Get an issue by its ID - Async version
async def get_issue_async(issue_key: str = issue_id) -> dict[str, object] | None:
    """Get an issue by its ID using the async API."""
    try:
        issue = await jira_async.issues.get_issue(issue_key)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue {issue_key}: {e}")
        return None


def get_issue_with_extra_params_sync(
    issue_key: str = issue_id,
) -> dict[str, object] | None:
    """Get an issue with additional query parameters using extra_params - Sync version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params: dict[str, str] = {
            "fields": "summary,description,status",
            "expand": "renderedFields,names,schema",
        }
        issue = jira_sync.issues.get_issue(issue_key, extra_params=extra_params)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue with extra params {issue_key}: {e}")
        return None


async def get_issue_with_extra_params_async(
    issue_key: str = issue_id,
) -> dict[str, object] | None:
    """Get an issue with additional query parameters using extra_params - Async version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params: dict[str, str] = {
            "fields": "summary,description,status",
            "expand": "renderedFields,names,schema",
        }
        issue = await jira_async.issues.get_issue(issue_key, extra_params=extra_params)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue with extra params {issue_key}: {e}")
        return None


def get_changelogs_sync(issue_key: str = issue_id) -> list[dict[str, object]] | None:
    """Get changelogs for an issue using the sync API."""
    try:
        changelogs = jira_sync.issues.get_changelogs(issue_key)
        pprint.pprint(changelogs)
        return changelogs
    except Exception as e:
        print(f"Error getting changelogs for issue {issue_key}: {e}")
        return None


async def get_changelogs_async(
    issue_key: str = issue_id,
) -> list[dict[str, object]] | None:
    """Get changelogs for an issue using the async API."""
    try:
        changelogs = await jira_async.issues.get_changelogs(issue_key)
        pprint.pprint(changelogs)
        return changelogs
    except Exception as e:
        print(f"Error getting changelogs for issue {issue_key}: {e}")
        return None


def edit_issue_sync(issue_key: str = issue_id) -> dict[str, object] | None:
    """Edit an issue using the sync API."""
    try:
        issue = jira_sync.issues.edit_issue(
            issue_id=issue_key,
            fields={"summary": "New summary"},
            notify_users=False,
            return_issue=True,
        )
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error editing issue {issue_key}: {e}")
        return None


async def edit_issue_async(issue_key: str = issue_id) -> dict[str, object] | None:
    """Edit an issue using the async API."""
    try:
        issue = await jira_async.issues.edit_issue(
            issue_id=issue_key,
            fields={"summary": "New summary"},
            notify_users=False,
            return_issue=True,
        )
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error editing issue {issue_key}: {e}")
        return None


def edit_issue_with_extra_data_sync(
    issue_key: str = issue_id,
) -> dict[str, object] | None:
    """Edit an issue with additional data parameters using extra_data - Sync version."""
    try:
        # Example of using extra_data to add additional data parameters
        extra_data: dict[str, object] = {
            "update": {
                "comment": [{"add": {"body": "Comment added via extra_data parameter"}}]
            }
        }
        issue = jira_sync.issues.edit_issue(
            issue_id=issue_key,
            fields={"summary": "Updated summary with extra data"},
            notify_users=False,
            return_issue=True,
            extra_data=extra_data,
        )
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error editing issue with extra data {issue_key}: {e}")
        return None


async def edit_issue_with_extra_data_async(
    issue_key: str = issue_id,
) -> dict[str, object] | None:
    """Edit an issue with additional data parameters using extra_data - Async version."""
    try:
        # Example of using extra_data to add additional data parameters
        extra_data: dict[str, object] = {
            "update": {
                "comment": [{"add": {"body": "Comment added via extra_data parameter"}}]
            }
        }
        issue = await jira_async.issues.edit_issue(
            issue_id=issue_key,
            fields={"summary": "Updated summary with extra data"},
            notify_users=False,
            return_issue=True,
            extra_data=extra_data,
        )
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error editing issue with extra data {issue_key}: {e}")
        return None


def test_sync() -> None:
    """Test sync API implementations."""
    print("=== Testing Sync API ===")
    print("Getting issue...")
    get_issue_sync()

    print("\nGetting issue with extra params...")
    get_issue_with_extra_params_sync()

    # print("\nGetting changelogs...")
    # get_changelogs_sync()

    # Uncomment the function you want to test
    # print("\nEditing issue...")
    # edit_issue_sync()

    # print("\nEditing issue with extra data...")
    # edit_issue_with_extra_data_sync()


def test_sync_with_context_manager() -> None:
    """Test sync API with auto-managed persistent clients."""
    print("=== Testing Sync API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPI()
    print("Getting issue with auto-managed clients...")
    try:
        issue = api.issues.get_issue(issue_id)
        pprint.pprint(issue)
    except Exception as e:
        print(f"Error getting issue {issue_id}: {e}")

    print("\nGetting issue with extra params...")
    try:
        extra_params: dict[str, str] = {
            "fields": "summary,description,status",
            "expand": "renderedFields,names,schema",
        }
        issue = api.issues.get_issue(issue_id, extra_params=extra_params)
        pprint.pprint(issue)
    except Exception as e:
        print(f"Error getting issue with extra params {issue_id}: {e}")

    print("Auto-managed clients handle resource cleanup automatically")


async def test_async() -> None:
    """Test async API implementations."""
    print("=== Testing Async API ===")
    print("Getting issue...")
    await get_issue_async()

    print("\nGetting issue with extra params...")
    await get_issue_with_extra_params_async()

    # print("\nGetting changelogs...")
    # await get_changelogs_async()

    # Uncomment the function you want to test
    # print("\nEditing issue...")
    # await edit_issue_async()

    # print("\nEditing issue with extra data...")
    # await edit_issue_with_extra_data_async()


async def test_async_with_context_manager() -> None:
    """Test async API with auto-managed persistent clients."""
    print("=== Testing Async API with Auto-Managed Clients ===")

    # API now uses auto-managed persistent clients
    api = JiraAPIAsync()
    print("Getting issue with auto-managed async clients...")
    try:
        issue = await api.issues.get_issue(issue_id)
        pprint.pprint(issue)
    except Exception as e:
        print(f"Error getting issue {issue_id}: {e}")

    print("\nGetting issue with extra params...")
    try:
        extra_params: dict[str, str] = {
            "fields": "summary,description,status",
            "expand": "renderedFields,names,schema",
        }
        issue = await api.issues.get_issue(issue_id, extra_params=extra_params)
        pprint.pprint(issue)
    except Exception as e:
        print(f"Error getting issue with extra params {issue_id}: {e}")

    print("Auto-managed async clients handle resource cleanup automatically")


def main() -> None:
    """Run both sync and async tests."""
    print("Starting Jira2py Issues API Tests...")
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
