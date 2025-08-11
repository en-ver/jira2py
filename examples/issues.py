from jira2py.issues import Issues
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()

# Change the issue ID to the one you want to test
issue_id = "PR-24446"


# Get an issue by its ID
def get_issue() -> None:
    with Issues() as issues:
        issue = issues.get_issue(issue_id)
        pprint.pprint(issue)


def get_changelogs() -> None:
    with Issues() as issues:
        changelogs = issues.get_changelogs(issue_id)
        pprint.pprint(changelogs)


def edit_issue() -> None:
    with Issues() as issues:
        issue = issues.edit_issue(
            issue_id=issue_id,
            fields={"summary": "New summary"},
            notify_users=False,
            return_issue=True,
        )
        pprint.pprint(issue)


# Alternative usage without context manager (manual resource management)
def get_issue_manual() -> None:
    issues = Issues()
    try:
        issue = issues.get_issue(issue_id)
        pprint.pprint(issue)
    finally:
        issues.close()


if __name__ == "__main__":
    pass
    # Uncomment the function you want to test
    # get_issue()
    # get_changelogs()
    # edit_issue()
    # get_issue_manual()
