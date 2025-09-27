import pprint

from dotenv import load_dotenv

from jira2py import IssueComments

# Make sure to set the environment variables in the .env file
load_dotenv()
comments = IssueComments()

# Change the issue ID to the one you want to test
issue_id = "PR-24458"


# Get the paginated list of comments for the issue
def get_comments(issue_key: str = issue_id) -> dict | None:
    """Get comments for an issue using the overloaded _request_jira method."""
    try:
        jira_comments = comments.get_comments(issue_id=issue_key, expand="renderedBody")
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments for issue {issue_key}: {e}")
        return None


def get_comments_with_extra_params(issue_key: str = issue_id) -> dict | None:
    """Get comments for an issue with additional query parameters."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params = {
            "startAt": 0,
            "maxResults": 5,
            "orderBy": "-created",  # Get newest comments first
        }
        jira_comments = comments.get_comments(
            issue_id=issue_key, expand="renderedBody", extra_params=extra_params
        )
        pprint.pprint(jira_comments)
        return jira_comments
    except Exception as e:
        print(f"Error getting comments with extra params for issue {issue_key}: {e}")
        return None


if __name__ == "__main__":
    print("Getting comments...")
    get_comments()

    print("\nGetting comments with extra params...")
    get_comments_with_extra_params()
