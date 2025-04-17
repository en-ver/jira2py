from jira2py import IssueSearch
from dotenv import load_dotenv
import os, pprint

load_dotenv()

jql = os.getenv("JQL", None)
search = IssueSearch()


# Search for issues using JQL
def enhanced_search():
    search_results = search.enhanced_search(jql=jql, fields=["summary"])
    pprint.pprint(search_results)


if __name__ == "__main__":
    enhanced_search()
