import pprint

from dotenv import load_dotenv

from jira2py.issue_comments import IssueComments

# Make sure to set the environment variables in the .env file
load_dotenv()

# Change the issue ID to the one you want to test
issue_id = "PR-25025"


def get_comments() -> None:
    with IssueComments() as issue_comments:
        comments = issue_comments.get_comments(issue_id)
        pprint.pprint(comments)


# Alternative usage without context manager (manual resource management)
def get_comments_manual() -> None:
    issue_comments = IssueComments()
    try:
        comments = issue_comments.get_comments(issue_id)
        pprint.pprint(comments)
    finally:
        issue_comments.close()


if __name__ == "__main__":
    pass
    # Uncomment the function you want to test
    get_comments()
    # get_comments_manual()
