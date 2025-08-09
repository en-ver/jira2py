from jira2py import IssueSearch
from dotenv import load_dotenv
import pprint

# Make sure to set the environment variables in the .env file
load_dotenv()

jql_query = "project = PR ORDER BY created DESC"


def enhanced_search():
    with IssueSearch() as issue_search:
        results = issue_search.enhanced_search(
            jql=jql_query,
            max_results=5,
            fields=["summary", "status", "assignee"],
        )
        pprint.pprint(results)


# Alternative usage without context manager (manual resource management)
def enhanced_search_manual():
    issue_search = IssueSearch()
    try:
        results = issue_search.enhanced_search(
            jql=jql_query,
            max_results=5,
            fields=["summary", "status", "assignee"],
        )
        pprint.pprint(results)
    finally:
        issue_search.close()


if __name__ == "__main__":
    pass
    # Uncomment the function you want to test
    # enhanced_search()
    # enhanced_search_manual()
