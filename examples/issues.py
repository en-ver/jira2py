from jira2py import Issues
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()

issues = Issues()
issue_id = "PR-24446"


# Get an issue by its ID
def get_issue():
    issue = issues.get_issue(issue_id)
    pprint.pprint(issue)


def get_changelogs():
    changelogs = issues.get_changelogs(issue_id)
    pprint.pprint(changelogs)


def edit_issue():
    issue = issues.edit_issue(
        issue_id=issue_id,
        fields={"summary": "New summary"},
        notify_users=False,
        return_issue=True,
    )
    pprint.pprint(issue)


if __name__ == "__main__":
    pass
    get_issue()
    get_changelogs()
    edit_issue()
