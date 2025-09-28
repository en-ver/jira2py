import asyncio
import pprint

from dotenv import load_dotenv

from jira2py import JiraAPI, JiraAPIAsync

# Make sure to set the environment variables in the .env file
load_dotenv()
jira_sync = JiraAPI()
jira_async = JiraAPIAsync()

# Change the issue ID to the one you want to test
issue_id = "PR-24458"


# Get the paginated list of comments for the issue - Sync version
def get_comments_sync(issue_key: str = issue_id) -> dict | None:
    """Get comments for an issue using the sync API."""
    try:
        jira_comments = jira_sync.comments.get_comments(
            issue_id=issue_key, expand="renderedBody"
        )
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments for issue {issue_key}: {e}")
        return None


# Get the paginated list of comments for the issue - Async version
async def get_comments_async(issue_key: str = issue_id) -> dict | None:
    """Get comments for an issue using the async API."""
    try:
        jira_comments = await jira_async.comments.get_comments(
            issue_id=issue_key, expand="renderedBody"
        )
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments for issue {issue_key}: {e}")
        return None


def get_comments_with_extra_params_sync(issue_key: str = issue_id) -> dict | None:
    """Get comments for an issue with additional query parameters - Sync version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params = {
            "startAt": 0,
            "maxResults": 5,
            "orderBy": "-created",  # Get newest comments first
        }
        jira_comments = jira_sync.comments.get_comments(
            issue_id=issue_key, expand="renderedBody", extra_params=extra_params
        )
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments with extra params for issue {issue_key}: {e}")
        return None


async def get_comments_with_extra_params_async(
    issue_key: str = issue_id,
) -> dict | None:
    """Get comments for an issue with additional query parameters - Async version."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params = {
            "startAt": 0,
            "maxResults": 5,
            "orderBy": "-created",  # Get newest comments first
        }
        jira_comments = await jira_async.comments.get_comments(
            issue_id=issue_key, expand="renderedBody", extra_params=extra_params
        )
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments with extra params for issue {issue_key}: {e}")
        return None


def test_sync():
    """Test sync API implementations."""
    print("=== Testing Sync API ===")
    print("Getting comments...")
    get_comments_sync()

    print("\nGetting comments with extra params...")
    get_comments_with_extra_params_sync()


async def test_async():
    """Test async API implementations."""
    print("=== Testing Async API ===")
    print("Getting comments...")
    await get_comments_async()

    print("\nGetting comments with extra params...")
    await get_comments_with_extra_params_async()


def main():
    """Run both sync and async tests."""
    print("Starting Jira2py Issue Comments API Tests...")
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
