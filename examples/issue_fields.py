from jira2py import IssueFields
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()


def get_fields():
    with IssueFields() as issue_fields:
        fields = issue_fields.get_fields()
        pprint.pprint(fields)


# Alternative usage without context manager (manual resource management)
def get_fields_manual():
    issue_fields = IssueFields()
    try:
        fields = issue_fields.get_fields()
        pprint.pprint(fields)
    finally:
        issue_fields.close()


if __name__ == "__main__":
    pass
    # Uncomment the function you want to test
    # get_fields()
    # get_fields_manual()
