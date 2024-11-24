# search.py

from jira2py import Jira

class Search(Jira):
    
    def __init__(self, jql:str, max_issues:int):
        
        self._jql = jql
        self._max_issues = max_issues
        self._max_results = 50
        self._next_page_token = None
        self.data = None
        self.issues = None

        self._get_data()

    def _get_data(self) -> None:
        
        issues = []

        while True:

            kwargs = {
                'method': 'GET',
                'context_path': 'search/jql',
                'params': {
                    'jql': self._jql,
                    'nextPageToken': self._next_page_token,
                    'maxResults': self._max_results,
                    'fields': 'key'
                }
            }

            response = self._request_jira(kwargs)

            issues.extend(response.get('issues', []))
            
            self.data = response
            self._next_page_token = response.get('nextPageToken', None)

            if self._next_page_token is None or len(issues) >= self._max_issues and self._max_issues > 0:
                break

        self.issues = issues

        return None