from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from jira2py import JiraAPI
from jira2py.helpers import (
    AttachmentHelpers,
    CommentHelpers,
    IssueHelpers,
    JiraHelpers,
    LinkHelpers,
    MetadataHelpers,
    SearchHelpers,
    WorklogHelpers,
)


def test_jira_helpers_exposes_grouped_helpers_for_one_api_instance() -> None:
    api = SimpleNamespace()

    helpers = JiraHelpers(cast(JiraAPI, api))

    assert helpers.api is api
    assert isinstance(helpers.issues, IssueHelpers)
    assert isinstance(helpers.search, SearchHelpers)
    assert isinstance(helpers.comments, CommentHelpers)
    assert isinstance(helpers.worklogs, WorklogHelpers)
    assert isinstance(helpers.attachments, AttachmentHelpers)
    assert isinstance(helpers.links, LinkHelpers)
    assert isinstance(helpers.metadata, MetadataHelpers)
    assert helpers.issues.api is api
    assert helpers.search.api is api
    assert helpers.comments.api is api
    assert helpers.worklogs.api is api
    assert helpers.attachments.api is api
    assert helpers.links.api is api
    assert helpers.metadata.api is api
