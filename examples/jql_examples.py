from jira2py import Jira
from dotenv import load_dotenv
import os

load_dotenv()

jira = Jira(
    jira_url=os.environ.get("JIRA_URL"),
    jira_user=os.environ.get("JIRA_USER"),
    jira_api_token=os.environ.get("JIRA_API_TOKEN"),
)
jql = os.getenv("JQL", None)

"""Create search instance"""
search = jira.jql(jql=jql)

"""Search and return all fields except priority, status category changedate, and status"""
search_results = search.get_page(
    fields=["*all", "-priority", "-statuscategorychangedate", "-status"],
    expand="names,changelog",
)

"""Get all pages of search results using paginated method"""
all_issues = search.get_all_pages(fields=["*all"], expand="names,changelog")

"""Follow https://en-ver.github.io/jira2py/ for more details"""
