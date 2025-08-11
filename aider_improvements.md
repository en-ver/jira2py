# Jira2Py Improvement Action Plan

## 1. Inconsistent Parameter Filtering
**Issue**: Different filtering approaches used in `jira_base.py` `_request_jira` method
**Solution**: Use the existing `_filter_none_values` helper method consistently

```python
# Current implementation - inconsistent
filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
filtered_data = {k: v for k, v in (data or {}).items() if v is not None}

# Should be consistent and use the helper method
filtered_params = self._filter_none_values(params)
filtered_data = self._filter_none_values(data)
```

## 2. Redundant Empty List Handling
**Issue**: Unnecessary conditional logic in `issue_search.py`
**Solution**: Remove the redundant empty list assignment

```python
# Current implementation - redundant
"reconcileIssues": reconcile_issues
if reconcile_issues is not None
else [],

# Should be simplified to
"reconcileIssues": reconcile_issues,
```

## 3. Missing Error Handling for Specific Cases
**Issue**: `_handle_response` method doesn't handle common HTTP error codes
**Solution**: Add specific error handling for 400, 401, 403, 404 status codes

## 4. Inconsistent Use of Helper Methods
**Issue**: `_build_api_url` method is defined but not used in `_request_jira`
**Solution**: Replace manual URL construction with the helper method

```python
# Current implementation - manual construction
api_path = context_path.strip("/")
url = f"{self._jira_url}/rest/api/3/{api_path}"

# Should use the existing method
url = self._build_api_url(context_path)
```

## 5. Add Type Hints for Return Values
**Issue**: Generic return types like `-> dict[str, Any]` and `-> list[dict[str, Any]]`
**Solution**: Create Pydantic models or type aliases for better type safety

## 6. Improve Documentation
**Issue**: Incomplete docstrings for public methods
**Solution**: Add comprehensive docstrings explaining:
- Expected return types
- Common exceptions that might be raised
- Example usage

## 7. Add Logging
**Issue**: No logging for API requests and retries
**Solution**: Implement logging to help with debugging and monitoring

## 8. Consider Adding a Main Client
**Issue**: Users need to instantiate multiple classes for different functionalities
**Solution**: Create a unified client that combines all functionality

```python
class JiraClient(JiraBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issues = Issues(*args, **kwargs)
        self.comments = IssueComments(*args, **kwargs)
        # etc.
```
