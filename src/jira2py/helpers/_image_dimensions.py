"""Private, in-memory image dimension parsing for managed Jira media."""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from typing import Literal

import imagesize

_MAX_IMAGE_AXIS = 65_535
_MAX_IMAGE_PIXELS = 89_478_485

_ImageFormat = Literal["png", "jpeg", "gif", "webp", "bmp", "tiff"]


@dataclass(frozen=True, slots=True)
class _ImageDimensions:
    width: int
    height: int


def _probe_image_dimensions(stream: io.BytesIO) -> _ImageDimensions | None:
    """Read dimensions from formats whose headers fit the 64-byte probe."""
    if not isinstance(stream, io.BytesIO):
        return None
    image_format = _image_format(stream)
    if image_format not in {"png", "gif", "webp", "bmp"}:
        return None
    return _dimensions_from_stream(stream, image_format)


def _parse_complete_image_dimensions(stream: io.BytesIO) -> _ImageDimensions | None:
    """Read dimensions from one complete supported image kept in memory."""
    if not isinstance(stream, io.BytesIO):
        return None
    image_format = _image_format(stream)
    if image_format is None:
        return None
    return _dimensions_from_stream(stream, image_format)


def _image_format(stream: io.BytesIO) -> _ImageFormat | None:
    """Recognize only the deliberately supported image formats."""
    try:
        stream.seek(0)
        header = stream.read(16)
    except (OSError, ValueError):
        return None
    finally:
        with contextlib.suppress(OSError, ValueError):
            stream.seek(0)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header[:6] in {b"GIF87a", b"GIF89a"}:
        return "gif"
    if header.startswith(b"\xff\xd8"):
        return "jpeg"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"
    if header.startswith(b"BM"):
        return "bmp"
    if header.startswith((b"MM\x00*", b"II*\x00", b"II+\x00")):
        return "tiff"
    return None


def _dimensions_from_stream(
    stream: io.BytesIO, image_format: _ImageFormat
) -> _ImageDimensions | None:
    """Contain parser sentinels and exceptions without accepting paths or URLs."""
    if image_format == "gif":
        return _gif_logical_screen_dimensions(stream)
    try:
        stream.seek(0)
        width, height = imagesize.get(stream, exif_rotation=True)
    except Exception:
        return None
    finally:
        with contextlib.suppress(OSError, ValueError):
            stream.seek(0)
    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width < 1
        or height < 1
    ):
        return None
    return _ImageDimensions(width, height)


def _gif_logical_screen_dimensions(stream: io.BytesIO) -> _ImageDimensions | None:
    """Read GIF's unsigned 16-bit logical-screen dimensions directly."""
    try:
        stream.seek(0)
        header = stream.read(10)
    except (OSError, ValueError):
        return None
    finally:
        with contextlib.suppress(OSError, ValueError):
            stream.seek(0)
    if len(header) != 10 or header[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    return _ImageDimensions(
        int.from_bytes(header[6:8], "little"),
        int.from_bytes(header[8:10], "little"),
    )


def _validate_image_dimensions(dimensions: _ImageDimensions) -> bool:
    """Apply Jira helper safety limits to otherwise valid intrinsic dimensions."""
    width = dimensions.width
    height = dimensions.height
    return (
        not isinstance(width, bool)
        and not isinstance(height, bool)
        and isinstance(width, int)
        and isinstance(height, int)
        and 0 < width <= _MAX_IMAGE_AXIS
        and 0 < height <= _MAX_IMAGE_AXIS
        and width * height <= _MAX_IMAGE_PIXELS
    )
