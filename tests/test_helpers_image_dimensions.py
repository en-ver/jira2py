"""Focused private managed-image dimension parser tests."""

from __future__ import annotations

import io
import struct

import pytest

from jira2py.helpers._image_dimensions import (
    _ImageDimensions,
    _parse_complete_image_dimensions,
    _probe_image_dimensions,
    _validate_image_dimensions,
)


def _png(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
        + b"\x00" * 35
    )


def _gif(width: int, height: int) -> bytes:
    return b"GIF89a" + struct.pack("<HH", width, height) + b"\x00" * 54


def _bmp(width: int, height: int) -> bytes:
    header = bytearray(64)
    header[:2] = b"BM"
    struct.pack_into("<ll", header, 18, width, height)
    return bytes(header)


def _webp_vp8(width: int, height: int) -> bytes:
    return (
        b"RIFF\x00\x00\x00\x00WEBPVP8 \x00\x00\x00\x00"
        + b"\x00" * 6
        + struct.pack("<HH", width, height)
        + b"\x00" * 34
    )


def _webp_vp8x(width: int, height: int) -> bytes:
    return (
        b"RIFF\x00\x00\x00\x00WEBPVP8X\x00\x00\x00\x00"
        + b"\x00" * 4
        + (width - 1).to_bytes(3, "little")
        + (height - 1).to_bytes(3, "little")
        + b"\x00" * 34
    )


def _webp_vp8l(width: int, height: int) -> bytes:
    value = (width - 1) | ((height - 1) << 14)
    return (
        b"RIFF\x00\x00\x00\x00WEBPVP8L\x00\x00\x00\x00\x2f"
        + value.to_bytes(4, "little")
        + b"\x00" * 39
    )


def _oriented_jpeg(width: int, height: int) -> bytes:
    exif = (
        b"Exif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x01"
        b"\x01\x12\x00\x03\x00\x00\x00\x01\x00\x06\x00\x00\x00\x00\x00\x00"
    )
    sof = (
        b"\x08"
        + struct.pack(">HH", height, width)
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    )
    return (
        b"\xff\xd8\xff\xe1"
        + struct.pack(">H", len(exif) + 2)
        + exif
        + b"\xff\xc0\x00\x11"
        + sof
        + b"\xff\xd9"
    )


def _oriented_tiff(width: int, height: int) -> bytes:
    entries = (
        struct.pack("<HHI4s", 256, 4, 1, struct.pack("<I", width))
        + struct.pack("<HHI4s", 257, 4, 1, struct.pack("<I", height))
        + struct.pack("<HHI4s", 274, 3, 1, struct.pack("<H", 6) + b"\x00\x00")
    )
    return b"II*\x00\x08\x00\x00\x00\x03\x00" + entries + b"\x00\x00\x00\x00"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (_png(640, 480), _ImageDimensions(640, 480)),
        (_gif(480, 640), _ImageDimensions(480, 640)),
        (_bmp(512, 512), _ImageDimensions(512, 512)),
        (_webp_vp8(720, 480), _ImageDimensions(720, 480)),
        (_webp_vp8x(800, 600), _ImageDimensions(800, 600)),
        (_webp_vp8l(321, 123), _ImageDimensions(321, 123)),
    ],
)
def test_probe_parses_64_byte_fast_path_formats(
    payload: bytes, expected: _ImageDimensions
) -> None:
    assert len(payload) >= 64
    assert _probe_image_dimensions(io.BytesIO(payload[:64])) == expected


def test_complete_parser_uses_exif_orientation_for_jpeg_and_tiff() -> None:
    assert _probe_image_dimensions(io.BytesIO(_oriented_jpeg(640, 480)[:64])) is None
    assert _parse_complete_image_dimensions(
        io.BytesIO(_oriented_jpeg(640, 480))
    ) == _ImageDimensions(480, 640)
    assert _parse_complete_image_dimensions(
        io.BytesIO(_oriented_tiff(640, 480))
    ) == _ImageDimensions(480, 640)


@pytest.mark.parametrize("width", [32_768, 40_000, 65_535])
def test_gif_uses_unsigned_logical_screen_dimensions(width: int) -> None:
    payload = _gif(width, 1)
    expected = _ImageDimensions(width, 1)

    assert _probe_image_dimensions(io.BytesIO(payload[:64])) == expected
    assert _parse_complete_image_dimensions(io.BytesIO(payload)) == expected
    gif87_payload = b"GIF87a" + payload[6:]
    assert _probe_image_dimensions(io.BytesIO(gif87_payload[:64])) == expected
    assert _parse_complete_image_dimensions(io.BytesIO(gif87_payload)) == expected
    assert _validate_image_dimensions(expected)


@pytest.mark.parametrize("payload", [b"GIF89a", b"GIF89a\x01\x00\x01"])
def test_gif_parser_rejects_truncated_logical_screen_header(payload: bytes) -> None:
    assert _probe_image_dimensions(io.BytesIO(payload)) is None
    assert _parse_complete_image_dimensions(io.BytesIO(payload)) is None


@pytest.mark.parametrize(
    "payload",
    [
        b"<svg width='1' height='1'/>",
        b"\x00\x00\x01\x00",  # ICO
        b"\x00\x00\x00\x0cjP  \r\n\x87\n",  # JPEG 2000
        b"\x00\x00\x00\x18ftypavif",  # AVIF
        b"\x89PNG\r\n\x1a\n",  # truncated PNG
    ],
)
def test_parser_rejects_unsupported_or_malformed_data(payload: bytes) -> None:
    stream = io.BytesIO(payload)
    assert _probe_image_dimensions(stream) is None
    assert _parse_complete_image_dimensions(stream) is None


@pytest.mark.parametrize(
    "dimensions",
    [
        _ImageDimensions(0, 1),
        _ImageDimensions(1, 0),
        _ImageDimensions(65_536, 1),
        _ImageDimensions(1, 65_536),
        _ImageDimensions(65_535, 65_535),
    ],
)
def test_dimension_safety_limits_reject_invalid_or_excessive_geometry(
    dimensions: _ImageDimensions,
) -> None:
    assert not _validate_image_dimensions(dimensions)


def test_dimension_safety_limits_accept_portrait_landscape_and_square() -> None:
    for dimensions in (
        _ImageDimensions(480, 640),
        _ImageDimensions(640, 480),
        _ImageDimensions(512, 512),
    ):
        assert _validate_image_dimensions(dimensions)


def test_parser_refuses_paths_and_urls() -> None:
    assert _parse_complete_image_dimensions("https://images.example/image.png") is None  # type: ignore[arg-type]


def test_parser_contains_dependency_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(stream: io.BytesIO, *, exif_rotation: bool) -> tuple[int, int]:
        assert isinstance(stream, io.BytesIO)
        assert exif_rotation
        raise RuntimeError("untrusted parser failure")

    monkeypatch.setattr("jira2py.helpers._image_dimensions.imagesize.get", fail)
    assert _parse_complete_image_dimensions(io.BytesIO(_png(1, 1))) is None
