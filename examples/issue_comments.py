import pprint

from dotenv import load_dotenv

from jira2py import IssueComments

# Make sure to set the environment variables in the .env file
load_dotenv()
comments = IssueComments()


# Get the paginated list of comments for the issue
def get_comments():
    jira_comments = comments.get_comments(issue_id="PR-24458", expand="renderedBody")
    pprint.pprint(jira_comments)


if __name__ == "__main__":
    get_comments()
