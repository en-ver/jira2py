import pytest
from jira2py.issues import Issues
   
class TestIssues:
    def test_get_issue_requires_auth(self):
        """Test that get_issue requires authentication"""
        issues = Issues()
        # Add your test logic here
        pass
