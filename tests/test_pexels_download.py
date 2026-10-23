"""Security and reliability of the optional Pexels media downloader."""

from pathlib import Path

import httpx
import pytest
from pydantic import HttpUrl

from meme_generator.infrastructure.pexels.download import (
    MAX_IMAGE_BYTES,
    download_photo,
)

HTTP_OK = 200
HTTP_REDIRECT = 302
CDN_IMAGE = HttpUrl('https://images.pexels.com/photos/test.jpeg')
EXTERNAL_IMAGE = HttpUrl('https://example.com/internal.jpeg')


def test_rejects_external_media_hosts(tmp_path: Path) -> None:
    """A hostile search payload cannot trigger server-side URL requests."""
    with (
        httpx.Client() as client,
        pytest.raises(ValueError, match='Pexels photo URLs'),
    ):
        download_photo(client, EXTERNAL_IMAGE, 1, tmp_path)


def test_rejects_html_and_removes_partial_file(tmp_path: Path) -> None:
    """A server error page cannot survive as a misleading JPEG path."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_OK,
            content=b'<html>',
            headers={'content-type': 'text/html'},
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='JPEG'),
    ):
        download_photo(client, CDN_IMAGE, 1, tmp_path)
    assert not (tmp_path / '1-pexels.jpg').exists()


def test_rejects_large_images(tmp_path: Path) -> None:
    """Oversized third-party payloads never remain on disk after failure."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_OK,
            content=b'x' * (MAX_IMAGE_BYTES + 1),
            headers={'content-type': 'image/jpeg'},
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='byte limit'),
    ):
        download_photo(client, CDN_IMAGE, 1, tmp_path)
    assert not (tmp_path / '1-pexels.jpg').exists()


def test_rejects_cdn_redirect(tmp_path: Path) -> None:
    """The image client must not follow unexpected URL redirects."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_REDIRECT,
            headers={'location': 'https://example.com/steal'},
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='redirects'),
    ):
        download_photo(client, CDN_IMAGE, 1, tmp_path)


def test_rejects_unsafe_ports(tmp_path: Path) -> None:
    """Non-standard ports are rejected before any network request."""
    source = HttpUrl('https://images.pexels.com:8080/photo.jpeg')
    with (
        httpx.Client() as client,
        pytest.raises(ValueError, match='Pexels photo URLs'),
    ):
        download_photo(client, source, 1, tmp_path)
