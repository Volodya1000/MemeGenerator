"""Security and size boundaries of external image downloads."""

from pathlib import Path

import httpx
import pytest

from meme_generator.infrastructure.commons.download import (
    download_image,
)
from meme_generator.infrastructure.commons.models import CommonsImage

IMAGE_WIDTH = 900
IMAGE_HEIGHT = 700


WIKIMEDIA_URL = 'https://upload.wikimedia.org/wikipedia/example.png'
HTTP_OK = 200


def sample_image(url: str) -> CommonsImage:
    """Return one typed third-party image record."""
    return CommonsImage(
        url=url,
        mime='image/png',
        width=IMAGE_WIDTH,
        height=IMAGE_HEIGHT,
    )


def test_downloads_approved_image(tmp_path: Path) -> None:
    """An approved image is stored at its expected scene position."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            HTTP_OK, headers={'content-type': 'image/png'}, content=b'png'
        ),
    )
    with httpx.Client(transport=transport) as client:
        path = download_image(
            client, sample_image(WIKIMEDIA_URL), 2, tmp_path
        )
    assert path.name == '2.png'
    assert path.read_bytes() == b'png'


def test_download_refuses_external_host(tmp_path: Path) -> None:
    """A malicious Commons payload cannot point to another domain."""
    with httpx.Client() as client:
        with pytest.raises(ValueError, match='Wikimedia'):
            download_image(
                client, sample_image('https://evil.test/image.png'), 1, tmp_path
            )


def test_download_refuses_invalid_content_type(tmp_path: Path) -> None:
    """HTML error pages must not be accepted as image assets."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            HTTP_OK, headers={'content-type': 'text/html'}, content=b'<html>'
        ),
    )
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError, match='response type'):
            download_image(
                client, sample_image(WIKIMEDIA_URL), 1, tmp_path
            )
    assert not (tmp_path / '1.png').exists()
