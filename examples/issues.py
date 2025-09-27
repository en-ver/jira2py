import pprint

from dotenv import load_dotenv

from jira2py import Issues

# Make sure to set the environment variables in the .env file
load_dotenv()
issues = Issues()

# Change the issue ID to the one you want to test
issue_id = "PR-24446"


# Get an issue by its ID
def get_issue(issue_key: str = issue_id) -> dict | None:
    """Get an issue by its ID using the overloaded _request_jira method."""
    try:
        issue = issues.get_issue(issue_key)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue {issue_key}: {e}")
        return None


def get_issue_with_extra_params(issue_key: str = issue_id) -> dict | None:
    """Get an issue with additional query parameters using extra_params."""
    try:
        # Example of using extra_params to add additional query parameters
        extra_params = {
            "fields": "summary,description,status",
            "expand": "renderedFields,names,schema",
        }
        issue = issues.get_issue(issue_key, extra_params=extra_params)
        pprint.pprint(issue)
        return issue
    except Exception as e:
        print(f"Error getting issue with extra params {issue_key}: {e}")
        return None


def get_changelogs(issue_key: str = issue_id) -> list[dict] | None:
    """Get changelogs for an issue using the overloaded _request_jira method."""
    try:
        changelogs = issues.get_changelogs(issue_key)
        pprint.pprint(changelogs)
        return changelogs
    except Exception as e:
        print(f"Error getting changelogs for issue {issue_key}: {e}")
        return None


def edit_issue(issue_key: str = issue_id) -> dict | None:
    """Edit an issue using the overloaded _request_jira method."""
    try:
        issue = issues.edit_issue(
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


def edit_issue_with_extra_data(issue_key: str = issue_id) -> dict | None:
    """Edit an issue with additional data parameters using extra_data."""
    try:
        # Example of using extra_data to add additional data parameters
        extra_data = {
            "update": {
                "comment": [{"add": {"body": "Comment added via extra_data parameter"}}]
            }
        }
        issue = issues.edit_issue(
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


if __name__ == "__main__":
    print("Getting issue...")
    get_issue()

    print("\nGetting issue with extra params...")
    get_issue_with_extra_params()

    # print("\nGetting changelogs...")
    # get_changelogs()

    # Uncomment the function you want to test
    # print("\nEditing issue...")
    # edit_issue()

    # print("\nEditing issue with extra data...")
    # edit_issue_with_extra_data()
