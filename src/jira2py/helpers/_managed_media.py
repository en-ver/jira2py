"""Private Jira-managed Markdown image coordination for helper writes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID

from adf_bridge import (
    AdfBridgeError,
    AdfDocument,
    ResolvedJiraImage,
    markdown_image_urls,
    verify_jira_media_readback,
)

from jira2py.api import JiraAPI

from ._adf import markdown_to_adf
from ._image_dimensions import (
    _ImageDimensions,
    _parse_complete_image_dimensions,
    _probe_image_dimensions,
    _validate_image_dimensions,
)
from .attachments import DEFAULT_MAX_DOWNLOAD
from .errors import JiraHelperOperationError, JiraHelperValidationError

_ATTACHMENT_CONTENT_PREFIX = "/rest/api/3/attachment/content/"
_MEDIA_HOST = "api.media.atlassian.com"


@dataclass(frozen=True, slots=True)
class _ConfiguredJiraOrigin:
    scheme: str
    hostname: str
    port: int


@dataclass(frozen=True, slots=True)
class _PreparedMarkdownDocument:
    document: AdfDocument
    resolved_images: tuple[ResolvedJiraImage, ...]

    @property
    def has_managed_images(self) -> bool:
        return bool(self.resolved_images)


@dataclass(frozen=True, slots=True)
class _ResolvedAttachment:
    media_id: str
    width: int
    height: int


class _JiraMarkdownWriteSession:
    """Resolve managed attachment images once for one helper write operation."""

    def __init__(self, api: JiraAPI, issue_key: str) -> None:
        self._api = api
        self._issue_key = issue_key
        self._origin: _ConfiguredJiraOrigin | None = None
        self._origin_loaded = False
        self._attachments: list[dict[str, Any]] | None = None
        self._resolved_attachments_by_id: dict[str, _ResolvedAttachment] = {}
        self._resolved_by_source_url: dict[str, ResolvedJiraImage] = {}

    def prepare(self, markdown: str) -> _PreparedMarkdownDocument:
        """Convert one Markdown field using only its consumed managed mappings."""
        try:
            image_urls = markdown_image_urls(markdown).value
        except AdfBridgeError as exc:
            raise JiraHelperValidationError(
                "Markdown input cannot be converted to Jira rich text."
            ) from exc

        resolutions: list[ResolvedJiraImage] = []
        resolution: ResolvedJiraImage | None = None
        origin = self._origin_for_images() if image_urls else None
        try:
            for source_url in dict.fromkeys(image_urls):
                classification, attachment_id = _classify_attachment_content_url(
                    source_url, origin
                )
                if classification == "malformed":
                    raise JiraHelperValidationError(
                        "Jira attachment-content image URL is malformed for the configured Jira site."
                    )
                if classification == "candidate":
                    if attachment_id is None:
                        raise JiraHelperValidationError(
                            "Jira attachment-content image URL is malformed for the configured Jira site."
                        )
                    resolution = self._resolve_source_url(source_url, attachment_id)
                    resolutions.append(resolution)
                    resolution = None

            try:
                document = markdown_to_adf(markdown, resolved_images=resolutions)
            except AdfBridgeError as exc:
                raise JiraHelperValidationError(
                    "Markdown input cannot be converted to Jira rich text."
                ) from exc
        except Exception:
            resolution = None
            resolutions.clear()
            self.discard_sensitive_state()
            raise

        return _PreparedMarkdownDocument(document, tuple(resolutions))

    def verify(self, prepared: _PreparedMarkdownDocument, persisted: Any) -> bool:
        """Return whether Jira preserved one managed document's submitted media."""
        if not prepared.has_managed_images:
            return True
        if not isinstance(persisted, dict):
            return False
        try:
            verify_jira_media_readback(
                prepared.document,
                persisted,
                resolved_images=prepared.resolved_images,
            )
        except Exception:
            return False
        return True

    def discard_sensitive_state(self) -> None:
        """Discard resolved media identities after a managed-write failure."""
        self._resolved_attachments_by_id.clear()
        self._resolved_by_source_url.clear()

    def _origin_for_images(self) -> _ConfiguredJiraOrigin | None:
        if not self._origin_loaded:
            self._origin = _configured_jira_origin(self._api.credentials.url)
            self._origin_loaded = True
        return self._origin

    def _resolve_source_url(
        self, source_url: str, attachment_id: str
    ) -> ResolvedJiraImage:
        cached = self._resolved_by_source_url.get(source_url)
        if cached is not None:
            return cached

        resolved_attachment = self._resolved_attachments_by_id.get(attachment_id)
        if resolved_attachment is None:
            attachment = self._find_issue_attachment(attachment_id)
            self._require_image_attachment(attachment)
            expected_size = self._require_attachment_size(attachment)
            dimensions = self._acquire_image_dimensions(attachment_id, expected_size)
            redirect_request_failed = False
            try:
                location = (
                    self._api.attachments._get_attachment_content_redirect_location(
                        attachment_id
                    )
                )
            except Exception:
                redirect_request_failed = True
            if redirect_request_failed:
                raise JiraHelperOperationError(
                    "Failed to obtain the Jira attachment media redirect."
                ) from None
            try:
                media_id = _media_id_from_redirect_location(location)
            finally:
                del location
            resolved_attachment = _ResolvedAttachment(
                media_id=media_id,
                width=dimensions.width,
                height=dimensions.height,
            )
            self._resolved_attachments_by_id[attachment_id] = resolved_attachment

        resolved = ResolvedJiraImage(
            source_url=source_url,
            media_id=resolved_attachment.media_id,
            collection="",
            width=resolved_attachment.width,
            height=resolved_attachment.height,
        )
        self._resolved_by_source_url[source_url] = resolved
        return resolved

    def _find_issue_attachment(self, attachment_id: str) -> dict[str, Any]:
        attachment_list_failed = False
        if self._attachments is None:
            try:
                self._attachments = self._api.attachments.get_issue_attachments(
                    self._issue_key
                )
            except Exception:
                attachment_list_failed = True
        attachments = self._attachments
        if attachment_list_failed or attachments is None:
            raise JiraHelperOperationError(
                "Failed to list issue attachments for managed image resolution."
            ) from None

        matches = [
            attachment
            for attachment in attachments
            if _attachment_id_matches(attachment.get("id"), attachment_id)
        ]
        if len(matches) != 1:
            raise JiraHelperValidationError(
                "The Markdown image URL must reference exactly one attachment associated with this issue."
            )
        return matches[0]

    @staticmethod
    def _require_image_attachment(attachment: dict[str, Any]) -> None:
        mime_type = attachment.get("mimeType")
        if (
            not isinstance(mime_type, str)
            or not mime_type.casefold().startswith("image/")
            or len(mime_type) == len("image/")
        ):
            raise JiraHelperValidationError(
                "The Markdown image URL must reference an associated image attachment."
            )

    @staticmethod
    def _require_attachment_size(attachment: dict[str, Any]) -> int:
        size = attachment.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            raise JiraHelperOperationError(
                "Jira attachment size metadata is unavailable for managed image resolution."
            )
        return size

    def _acquire_image_dimensions(
        self, attachment_id: str, expected_size: int
    ) -> _ImageDimensions:
        prefix_end = min(63, expected_size - 1)
        prefix_read_failed = False
        try:
            prefix = self._api.attachments._get_attachment_content_bounded(
                attachment_id,
                expected_size=expected_size,
                max_bytes=DEFAULT_MAX_DOWNLOAD,
                byte_range=(0, prefix_end),
            )
        except Exception:
            prefix_read_failed = True
        if prefix_read_failed:
            raise JiraHelperOperationError(
                "Failed to read Jira attachment content for managed image resolution."
            ) from None

        prefix_complete = prefix.complete
        try:
            dimensions = (
                _parse_complete_image_dimensions(prefix.body)
                if prefix_complete
                else _probe_image_dimensions(prefix.body)
            )
        finally:
            prefix.body.close()
            del prefix

        if (
            dimensions is None
            and not prefix_complete
            and expected_size > DEFAULT_MAX_DOWNLOAD
        ):
            raise JiraHelperValidationError(
                "The image format requires a complete attachment larger than the managed image limit."
            )
        if dimensions is None and not prefix_complete:
            full_read_failed = False
            try:
                full = self._api.attachments._get_attachment_content_bounded(
                    attachment_id,
                    expected_size=expected_size,
                    max_bytes=DEFAULT_MAX_DOWNLOAD,
                )
            except Exception:
                full_read_failed = True
            if full_read_failed:
                raise JiraHelperOperationError(
                    "Failed to read Jira attachment content for managed image resolution."
                ) from None
            try:
                dimensions = _parse_complete_image_dimensions(full.body)
            finally:
                full.body.close()
                del full

        if dimensions is None:
            raise JiraHelperValidationError(
                "The attachment is not a supported managed image format."
            )
        if not _validate_image_dimensions(dimensions):
            raise JiraHelperValidationError(
                "The attachment image dimensions exceed managed image safety limits."
            )
        return dimensions


def _validate_create_markdown_images(
    api: JiraAPI, markdown_values: Iterable[str]
) -> None:
    """Reject attachment-content image URLs before a create request has an issue key."""
    origin: _ConfiguredJiraOrigin | None = None
    origin_loaded = False
    for markdown in markdown_values:
        try:
            image_urls = markdown_image_urls(markdown).value
        except AdfBridgeError as exc:
            raise JiraHelperValidationError(
                "Markdown input cannot be converted to Jira rich text."
            ) from exc
        if image_urls and not origin_loaded:
            origin = _configured_jira_origin(api.credentials.url)
            origin_loaded = True
        for source_url in image_urls:
            classification, _ = _classify_attachment_content_url(source_url, origin)
            if classification in {"candidate", "malformed"}:
                raise JiraHelperValidationError(
                    "Jira attachment-content image URLs cannot be used while creating "
                    "an issue. Create the issue first, upload the image to the returned "
                    "issue key, then edit the complete rich-text field using the upload "
                    "result's content URL."
                )


def _configured_jira_origin(url: str) -> _ConfiguredJiraOrigin | None:
    try:
        parsed = urlsplit(url)
        port = parsed.port if parsed.port is not None else 443
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or port != 443
    ):
        return None
    return _ConfiguredJiraOrigin("https", parsed.hostname, port)


def _classify_attachment_content_url(
    source_url: str, origin: _ConfiguredJiraOrigin | None
) -> tuple[Literal["external", "candidate", "malformed"], str | None]:
    """Classify only canonical absolute URLs on the configured Jira origin."""
    if origin is None:
        return "external", None
    try:
        parsed = urlsplit(source_url)
    except ValueError:
        return "external", None
    if not parsed.scheme or not parsed.netloc:
        return "external", None
    if (
        parsed.scheme != origin.scheme
        or parsed.hostname != origin.hostname
        or not _is_attachment_content_namespace(parsed.path)
    ):
        return "external", None
    try:
        port = parsed.port if parsed.port is not None else 443
        if port != origin.port:
            return "external", None
    except ValueError:
        return "malformed", None

    attachment_id = parsed.path.removeprefix(_ATTACHMENT_CONTENT_PREFIX)
    if (
        parsed.username is None
        and parsed.password is None
        and "?" not in source_url
        and "#" not in source_url
        and _is_canonical_positive_decimal(attachment_id)
    ):
        return "candidate", attachment_id
    return "malformed", None


def _is_attachment_content_namespace(path: str) -> bool:
    return path == _ATTACHMENT_CONTENT_PREFIX.removesuffix("/") or path.startswith(
        _ATTACHMENT_CONTENT_PREFIX
    )


def _is_canonical_positive_decimal(value: str) -> bool:
    return value.isascii() and value.isdecimal() and value[0] != "0"


def _attachment_id_matches(value: Any, attachment_id: str) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value == int(attachment_id)
    return (
        isinstance(value, str)
        and value.isascii()
        and value.isdecimal()
        and int(value) == int(attachment_id)
    )


def _media_id_from_redirect_location(location: str) -> str:
    """Validate Jira's observed 303 target without retaining its signed URL."""
    media_id = _validated_media_id_from_redirect_location(location)
    del location
    if media_id is None:
        raise JiraHelperOperationError(
            "Jira attachment content redirect is not an approved Media Services URL."
        )
    return media_id


def _validated_media_id_from_redirect_location(location: str) -> str | None:
    """Return a canonical media ID only when a redirect target is approved."""
    try:
        parsed = urlsplit(location)
        port = parsed.port if parsed.port is not None else 443
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.hostname != _MEDIA_HOST
        or port != 443
        or "#" in location
        or ("?" in location and not parsed.query)
    ):
        return None

    prefix = "/file/"
    suffix = "/binary"
    if not parsed.path.startswith(prefix) or not parsed.path.endswith(suffix):
        return None
    media_id = parsed.path[len(prefix) : -len(suffix)]
    try:
        media_uuid = UUID(media_id)
    except ValueError:
        return None
    return media_id if str(media_uuid) == media_id else None
