from jira2py import Jira
import json, os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Create a Jira instance
jira = Jira(
    url=os.getenv("JIRA_URL", ""),
    user=os.getenv("JIRA_USER", ""),
    api_token=os.getenv("JIRA_API_TOKEN", ""),
)

jql = 'statuscategory IN ("In Progress")'

# Search and return all fields except priority, status category changedate, and status
# search = jira.search().jql(
#     jql=jql,
#     fields=['*all','-priority', '-statuscategorychangedate', '-status']
# )

# print(json.dumps(search['issues'][0], indent=4))

# Get all pages of search results

all_issues = []
search = {}

while True:

    next_page_token = search.get("nextPageToken", None)
    if not next_page_token and search or len(all_issues) >= 50:
        break

    # Fetch the next page of search results
    search = jira.search().jql(
        jql=jql, next_page_token=next_page_token, fields=["*all"], expand="names"
    )

    all_issues.extend(search["issues"])

print(len(all_issues))
print(json.dumps(all_issues[0], indent=4))
