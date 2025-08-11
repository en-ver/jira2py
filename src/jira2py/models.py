from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class JiraIssue(BaseModel):
    """Pydantic model for Jira issue responses."""
    id: Optional[str] = None
    key: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    # Allow any additional fields
    class Config:
        extra = "allow"


class JiraComment(BaseModel):
    """Pydantic model for Jira comment responses."""
    id: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    # Allow any additional fields
    class Config:
        extra = "allow"


class JiraField(BaseModel):
    """Pydantic model for Jira field definitions."""
    id: Optional[str] = None
    name: Optional[str] = None
    schema_: Optional[Dict[str, Any]] = None
    # Allow any additional fields
    class Config:
        extra = "allow"


class JiraSearchResult(BaseModel):
    """Pydantic model for Jira search results."""
    startAt: Optional[int] = None
    maxResults: Optional[int] = None
    total: Optional[int] = None
    issues: Optional[List[JiraIssue]] = None
    nextPageToken: Optional[str] = None
    # Allow any additional fields
    class Config:
        extra = "allow"
