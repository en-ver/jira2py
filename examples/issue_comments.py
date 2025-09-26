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


if __name__ == "__main__":
    print("Getting comments...")
    get_comments()
