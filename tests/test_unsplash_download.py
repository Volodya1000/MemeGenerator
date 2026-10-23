"""Reject unsafe Unsplash CDN addresses and invalid image responses."""

from pathlib import Path

import httpx
import pytest
from pydantic import HttpUrl

from meme_generator.infrastructure.unsplash.download import (
    MAX_IMAGE_BYTES,
    download_photo,
    validate_download_location,
)

HTTP_OK = 200
HTTP_REDIRECT = 302
GOOD_IMAGE = HttpUrl('https://images.unsplash.com/photo.jpg')


def test_external_photo_host_is_blocked(tmp_path: Path) -> None:
    """Protect CI runners from arbitrary network requests."""
    with (
        httpx.Client() as client,
        pytest.raises(ValueError, match='Untrusted Unsplash'),
    ):
        download_photo(
            client, HttpUrl('https://example.com/private'), 1, tmp_path
        )


def test_external_download_tracking_is_blocked() -> None:
    """Tracking must point to the specific Unsplash photo ID."""
    with pytest.raises(ValueError, match='Untrusted Unsplash'):
        validate_download_location(
            HttpUrl('https://api.unsplash.com/photos/other/download'), 'id'
        )


@pytest.mark.parametrize('mime', ['text/html', 'image/png'])
def test_incorrect_mime_is_rejected(tmp_path: Path, mime: str) -> None:
    """Never treat HTML or arbitrary bytes as a valid JPEG."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_OK,
            content=b'invalid',
            headers={'content-type': mime},
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='JPEG'),
    ):
        download_photo(client, GOOD_IMAGE, 1, tmp_path)
    assert not (tmp_path / '1-unsplash.jpg').exists()


def test_oversized_photo_is_removed(tmp_path: Path) -> None:
    """Bound memory and disk consumption in CI."""
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
        download_photo(client, GOOD_IMAGE, 1, tmp_path)
    assert not (tmp_path / '1-unsplash.jpg').exists()


def test_redirect_is_not_followed(tmp_path: Path) -> None:
    """Do not follow CDN redirects to a potentially hostile endpoint."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_REDIRECT,
            headers={'location': 'https://evil.example'},
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='redirects'),
    ):
        download_photo(client, GOOD_IMAGE, 1, tmp_path)
