import pprint

from dotenv import load_dotenv

from jira2py import IssueSearch

# Make sure to set the environment variables in the .env file
load_dotenv()
search = IssueSearch()

# Change the JQL query to the one you want to test
jql = "project IN (PR)"


# Search for issues using JQL
def enhanced_search(query: str = jql) -> dict | None:
    """Search for issues using JQL with the overloaded _request_jira method."""
    try:
        search_results = search.enhanced_search(jql=query, fields=["summary"])
        pprint.pprint(search_results)
        return search_results
    except Exception as e:
        print(f"Error searching issues with query '{query}': {e}")
        return None


if __name__ == "__main__":
    print("Performing enhanced search...")
    enhanced_search()
