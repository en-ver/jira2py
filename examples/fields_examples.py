from jira2py import Jira
from dotenv import load_dotenv
import os

load_dotenv()

jira = Jira(
    jira_url=os.environ.get("JIRA_URL"),
    jira_user=os.environ.get("JIRA_USER"),
    jira_api_token=os.environ.get("JIRA_API_TOKEN"),
)

"""Create fields instance"""
fields = jira.fields()

"""Get the list of Jira fields with its metadata"""
jira_fields = fields.get()

"""Get the field id by its name"""
field_ids = fields.get_field_id(["Summary", "Reporter", "Parent"])

"""Get the field id by its id"""
field_names = fields.get_field_name(["summary", "reporter", "parent"])

"""Follow https://en-ver.github.io/jira2py/ for more details"""
