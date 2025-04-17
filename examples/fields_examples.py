from jira2py import Jira
from dotenv import load_dotenv
import os
import pprint

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

jira = Jira(
    jira_url=os.environ.get("JIRA_URL"),
    jira_user=os.environ.get("JIRA_USER"),
    jira_api_token=os.environ.get("JIRA_API_TOKEN"),
)

"""Create fields instance"""
fields = jira.issue_fields()

"""Get the list of Jira fields with its metadata"""
jira_fields = fields.get_fields()

pprint.pprint(jira_fields)
