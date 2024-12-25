from jira2py import Jira
import os
from dotenv import load_dotenv

"""Load .env variables"""
load_dotenv()

"""Create a Jira instance"""
jira = Jira(
    url=os.getenv("JIRA_URL", ""),
    user=os.getenv("JIRA_USER", ""),
    api_token=os.getenv("JIRA_API_TOKEN", ""),
)

"""Create an Issue instance"""
issue = jira.issue()

"""Get Issue details"""
response = issue.get("PRJ-1111")  # issue object including the issue details
names = response["names"]  # field ID-name mapping
fields = response["fields"]  # field ID-name mapping
status = fields["status"]["name"]  # status field value
summary = fields["summary"]  # summary field value

"""Update "summary" field"""
response = issue.edit(key="PRJ-1111", fields={"summary": f"Test summary"})

"""Get changelog of the issue"""
search_first_page = issue.get_changelogs(
    "PRJ-1111"
)  # Long changelogs returned paginated
search_second_page = issue.get_changelogs(
    "PRJ-1111", start_at=50, max_results=50
)  # set the # of item to start from load and items to load to get the next page of results
