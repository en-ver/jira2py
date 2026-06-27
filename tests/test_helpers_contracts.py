from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import jira2py.helpers as helpers
from jira2py.helpers import (
    AttachmentDownloadError,
    AttachmentDownloadPlan,
    AttachmentError,
    AttachmentHelpers,
    AuthHelpers,
    CommentHelpers,
    FieldMeta,
    FieldSchema,
    FilterSearchResult,
    FiltersHelpers,
    HelperResult,
    IssueHelpers,
    IssueTransition,
    JiraFilter,
    JiraHelperConfigError,
    JiraHelperOperationError,
    JiraHelpers,
    JiraHelperValidationError,
    JiraPriority,
    JiraStatus,
    JiraWorklog,
    LinkHelpers,
    MetadataHelpers,
    SearchHelpers,
    StatusCategory,
    WorklogHelpers,
    WorklogPage,
)
from jira2py.helpers.errors import JiraHelperError
from jira2py.helpers.models import AttachmentMeta


def test_helper_result_supports_text_only_and_raw_payloads() -> None:
    text_only = HelperResult.text_only("hello")
    assert text_only.text == "hello"
    assert text_only.data is None
    assert text_only.raw_content is None
    assert text_only.has_raw_output is False

    with_data = HelperResult.with_data(
        "done",
        {"key": "PROJ-123"},
        raw_content='{"key":"PROJ-123"}',
    )
    assert with_data.text == "done"
    assert with_data.data == {"key": "PROJ-123"}
    assert with_data.raw_content == '{"key":"PROJ-123"}'
    assert with_data.has_raw_output is True


def test_helper_errors_keep_message_and_details() -> None:
    error = JiraHelperOperationError(
        "Failed to update issue PROJ-123",
        details={"issue_key": "PROJ-123", "operation": "edit"},
    )

    assert str(error) == "Failed to update issue PROJ-123"
    assert error.details == {"issue_key": "PROJ-123", "operation": "edit"}


def test_helper_error_hierarchy_covers_expected_contracts() -> None:
    assert isinstance(JiraHelperValidationError("bad input"), JiraHelperError)
    assert isinstance(JiraHelperConfigError("missing token"), JiraHelperError)
    assert isinstance(AttachmentError("too large"), JiraHelperError)
    assert isinstance(AttachmentDownloadError("download failed"), AttachmentError)


def test_field_meta_parses_jira_schema_and_dumps_renamed_field() -> None:
    field = FieldMeta.model_validate(
        {
            "fieldId": "summary",
            "name": "Summary",
            "schema": {"type": "string"},
        }
    )

    assert field.jira_schema == FieldSchema(type="string")
    assert "jira_schema" in FieldMeta.model_fields
    assert "schema" not in FieldMeta.model_fields

    dumped = field.model_dump()
    assert dumped["jira_schema"] == {"type": "string", "custom": ""}
    assert "schema" not in dumped


def test_field_meta_accepts_python_construction_by_jira_schema_name() -> None:
    field = FieldMeta.model_validate(
        {
            "fieldId": "summary",
            "name": "Summary",
            "jira_schema": {"type": "string"},
        }
    )

    assert field.jira_schema == FieldSchema(type="string")


def test_attachment_download_plan_is_available_as_foundational_model() -> None:
    resolved_output = Path("debug.log").resolve()
    plan = AttachmentDownloadPlan(
        attachment_id="10001",
        filename="debug.log",
        output_file=str(resolved_output),
        resolved_output=resolved_output,
        meta=AttachmentMeta(id=10001, filename="debug.log", size=1536),
        content_url="https://example.atlassian.net/rest/api/3/attachment/content/10001",
    )

    assert plan.filename == "debug.log"
    assert plan.meta.size == 1536


def test_public_helpers_exports_grouped_helper_api_without_private_internals() -> None:
    assert "HelperResult" in helpers.__all__
    assert "JiraHelpers" in helpers.__all__
    assert "IssueHelpers" in helpers.__all__
    assert "IssueTransition" in helpers.__all__
    assert "SearchHelpers" in helpers.__all__
    assert "CommentHelpers" in helpers.__all__
    assert "AuthHelpers" in helpers.__all__
    assert "FiltersHelpers" in helpers.__all__
    assert "WorklogHelpers" in helpers.__all__
    assert "JiraWorklog" in helpers.__all__
    assert "WorklogPage" in helpers.__all__
    assert "AttachmentHelpers" in helpers.__all__
    assert "LinkHelpers" in helpers.__all__
    assert "MetadataHelpers" in helpers.__all__
    assert helpers.JiraHelpers is JiraHelpers
    assert helpers.IssueHelpers is IssueHelpers
    assert helpers.IssueTransition is IssueTransition
    assert helpers.SearchHelpers is SearchHelpers
    assert helpers.CommentHelpers is CommentHelpers
    assert helpers.AuthHelpers is AuthHelpers
    assert helpers.FiltersHelpers is FiltersHelpers
    assert helpers.WorklogHelpers is WorklogHelpers
    assert helpers.JiraWorklog is JiraWorklog
    assert helpers.WorklogPage is WorklogPage
    assert helpers.AttachmentHelpers is AttachmentHelpers
    assert helpers.LinkHelpers is LinkHelpers
    assert helpers.MetadataHelpers is MetadataHelpers
    assert "adf_to_markdown" not in helpers.__all__
    assert "format_issue_full" not in helpers.__all__
    assert not hasattr(helpers, "adf_to_markdown")
    assert not hasattr(helpers, "format_issue_full")


def test_filter_models_are_available_as_foundational_exports() -> None:
    result = FilterSearchResult.model_validate(
        {
            "values": [
                {
                    "id": "10100",
                    "name": "My open issues",
                    "owner": {"displayName": "Alice", "accountId": "acct-1"},
                    "jql": "project = PROJ",
                }
            ]
        }
    )

    assert isinstance(result.values[0], JiraFilter)
    assert JiraPriority.model_validate({"id": "1", "name": "High"}).name == "High"
    assert JiraStatus.model_validate(
        {
            "id": "3",
            "name": "Done",
            "statusCategory": {"id": 3, "key": "done", "name": "Done"},
        }
    ).statusCategory == StatusCategory(id=3, key="done", name="Done", colorName=None)


def test_importing_helper_models_with_warning_errors_enabled_succeeds() -> None:
    subprocess.run(  # noqa: S603 - fixed interpreter invocation for fresh-import validation
        [
            sys.executable,
            "-W",
            "error::UserWarning",
            "-c",
            "import jira2py.helpers.models",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
