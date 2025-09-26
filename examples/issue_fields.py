import pprint

from dotenv import load_dotenv

from jira2py import IssueFields

# Make sure to set the environment variables in the .env file
load_dotenv()
fields = IssueFields()


# Get all Jira fields with its metadata
def get_all_fields() -> list | None:
    """Get all Jira fields using the overloaded _request_jira method."""
    try:
        jira_fields = fields.get_fields()
        pprint.pprint(jira_fields)
        return jira_fields
    except Exception as e:
        print(f"Error getting Jira fields: {e}")
        return None


if __name__ == "__main__":
    print("Getting all fields...")
    get_all_fields()
