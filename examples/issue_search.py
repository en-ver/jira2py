from jira2py import IssueSearch
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()

jql = "project IN (PR) AND statuscategory IN ('In Progress')"
search = IssueSearch()


# Search for issues using JQL
def enhanced_search():
    search_results = search.enhanced_search(jql=jql, fields=["summary"])
    pprint.pprint(search_results)


if __name__ == "__main__":
    pass
    enhanced_search()
