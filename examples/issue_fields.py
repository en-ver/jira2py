from jira2py import IssueFields
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()
fields = IssueFields()


# Get all Jira fields with its metadata
def get_all_fields():
    jira_fields = fields.get_fields()
    pprint.pprint(jira_fields)


if __name__ == "__main__":
    pass
    get_all_fields()
