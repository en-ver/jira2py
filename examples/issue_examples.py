from jira2py import Jira
from dotenv import load_dotenv
import os

load_dotenv()

jira = Jira(
    jira_url=os.environ.get("JIRA_URL"),
    jira_user=os.environ.get("JIRA_USER"),
    jira_api_token=os.environ.get("JIRA_API_TOKEN"),
)
issue_key = os.environ.get("ISSUE_KEY")

"""Create an Issue instance"""
issue = jira.issue(issue_key)

"""Get Issue details"""
issue_json = issue.get(fields=["status", "summary"])  # Raw JSON reposnse form jira API
names = issue_json["names"]  # Field ID-name mapping
fields = issue_json["fields"]  # Fields of the issues
status = issue_json["fields"]["status"]["name"]  # Status field value
summary = issue_json.get("fields", {}).get("summary", None)  # Summary field value

"""Update "summary" field"""
enable_edit = False  # put here True to let teh script proceed with edit
if enable_edit:
    edit_response_json = issue.edit(fields={"summary": f"Test summary"})

"""Get the the first page of the changelog"""
changelog_page_json = issue.changelog_page()

"""Get the changelog first page filtered by field ids"""
changelog_page_json_filtered = issue.changelog_page(fields=["issuetype", "labels"])

"""Get full changelog of the issue"""
full_changelog_list = issue.changelog_all_pages()

"""Get full changelog of the issue filtered by field ids"""
full_changelog_list_filtered = issue.changelog_all_pages(fields=["issuetype", "labels"])

"""Follow https://en-ver.github.io/jira2py/ for more details"""
