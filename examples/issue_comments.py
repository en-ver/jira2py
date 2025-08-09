from jira2py import IssueComments
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()

# Change the issue ID to the one you want to test
issue_id = "PR-24446"


def get_comments():
    with IssueComments() as issue_comments:
        comments = issue_comments.get_comments(issue_id)
        pprint.pprint(comments)


def add_comment():
    with IssueComments() as issue_comments:
        comment = issue_comments.add_comment(
            issue_id=issue_id,
            body="This is a test comment added via the API",
        )
        pprint.pprint(comment)


# Alternative usage without context manager (manual resource management)
def get_comments_manual():
    issue_comments = IssueComments()
    try:
        comments = issue_comments.get_comments(issue_id)
        pprint.pprint(comments)
    finally:
        issue_comments.close()


if __name__ == "__main__":
    pass
    # Uncomment the function you want to test
    # get_comments()
    # add_comment()
    # get_comments_manual()
