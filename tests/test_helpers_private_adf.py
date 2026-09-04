from __future__ import annotations

import pytest

import jira2py.helpers._adf as adf


def test_markdown_to_adf_returns_empty_doc_for_blank_input() -> None:
    assert adf.markdown_to_adf("   ") == {"type": "doc", "version": 1, "content": []}


def test_detect_adf_field_ids_includes_system_and_custom_textareas() -> None:
    metadata = [
        {
            "id": "customfield_10001",
            "schema": {
                "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textarea"
            },
        },
        {
            "id": "customfield_10002",
            "schema": {
                "custom": "com.atlassian.jira.plugin.system.customfieldtypes:textfield"
            },
        },
    ]

    assert adf.detect_adf_field_ids(metadata) == {
        "customfield_10001",
        "description",
        "environment",
    }


def test_convert_markdown_fields_only_converts_known_adf_fields() -> None:
    converted = adf.convert_markdown_fields(
        {"customfield_10001": "Hello **world**", "summary": "Fix thing"},
        {"customfield_10001"},
    )

    assert converted == {
        "customfield_10001": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Hello "},
                        {
                            "type": "text",
                            "text": "world",
                            "marks": [{"type": "strong"}],
                        },
                    ],
                }
            ],
        },
        "summary": "Fix thing",
    }


def test_convert_markdown_fields_leaves_raw_adf_unchanged() -> None:
    raw_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "mention", "attrs": {"id": "raw:ID"}}],
            }
        ],
    }

    converted = adf.convert_markdown_fields(
        {"customfield_10001": raw_adf},
        {"customfield_10001"},
    )

    assert converted["customfield_10001"] is raw_adf


@pytest.mark.parametrize(
    ("markdown", "content"),
    [
        (
            "[~ACCOUNTID:557057:User:AbC]",
            [
                {
                    "type": "mention",
                    "attrs": {"id": "557057:User:AbC"},
                }
            ],
        ),
        (
            r"\[~accountId:escaped:ID]",
            [{"type": "text", "text": "[~accountId:escaped:ID]"}],
        ),
        (
            "`[~accountId:code:ID]`",
            [
                {
                    "type": "text",
                    "text": "[~accountId:code:ID]",
                    "marks": [{"type": "code"}],
                }
            ],
        ),
        (
            "[link [~accountId:link:ID]](https://example.com)",
            [
                {
                    "type": "text",
                    "text": "link [~accountId:link:ID]",
                    "marks": [
                        {"type": "link", "attrs": {"href": "https://example.com"}}
                    ],
                }
            ],
        ),
        ("[~accountId:]", [{"type": "text", "text": "[~accountId:]"}]),
        (
            "[~account:wrong-label]",
            [{"type": "text", "text": "[~account:wrong-label]"}],
        ),
        ("[~accountId:unclosed", [{"type": "text", "text": "[~accountId:unclosed"}]),
    ],
)
def test_markdown_to_adf_handles_jira_mention_syntax(
    markdown: str,
    content: list[dict[str, object]],
) -> None:
    assert adf.markdown_to_adf(markdown) == {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": content}],
    }


def test_markdown_to_adf_keeps_mentions_in_image_text_literal() -> None:
    assert adf.markdown_to_adf(
        "![image [~accountId:image:ID]](https://example.com/image.png)"
    ) == {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "mediaSingle",
                "attrs": {"layout": "center"},
                "content": [
                    {
                        "type": "media",
                        "attrs": {
                            "type": "external",
                            "url": "https://example.com/image.png",
                            "alt": "image [~accountId:image:ID]",
                        },
                    }
                ],
            }
        ],
    }


def test_adf_to_markdown_falls_back_to_plain_text_extraction(monkeypatch) -> None:
    class BrokenDocument:
        def __init__(self, _value) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(adf, "Document", BrokenDocument)

    value = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Top"},
                    {"type": "text", "text": "level"},
                ],
            },
            {
                "type": "nestedExpand",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Nested text"}],
                    }
                ],
            },
        ],
    }

    assert adf.adf_to_markdown(value) == "Top level Nested text"
