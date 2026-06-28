"""High-level grouped helper facade for jira2py."""

from __future__ import annotations

from jira2py.api import JiraAPI

from .attachments import AttachmentHelpers
from .auth import AuthHelpers
from .comments import CommentHelpers
from .filters import FiltersHelpers
from .issues import IssueHelpers
from .links import LinkHelpers
from .metadata import MetadataHelpers
from .search import SearchHelpers
from .worklogs import WorklogHelpers


class JiraHelpers:
    """Facade exposing grouped high-level Jira helper operations."""

    def __init__(self, api: JiraAPI) -> None:
        self.api = api
        self.auth = AuthHelpers(api)
        self.issues = IssueHelpers(api)
        self.search = SearchHelpers(api)
        self.comments = CommentHelpers(api)
        self.worklogs = WorklogHelpers(api)
        self.attachments = AttachmentHelpers(api)
        self.links = LinkHelpers(api)
        self.metadata = MetadataHelpers(api)
        self.filters = FiltersHelpers(api)


__all__ = ["JiraHelpers"]
