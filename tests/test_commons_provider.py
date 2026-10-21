"""Integration-style contract tests at the Commons HTTP boundary."""

from pathlib import Path

import httpx
import pytest

from meme_generator.infrastructure.commons import CommonsImageProvider

HTTP_OK = 200
IMAGE_WIDTH = 960
IMAGE_HEIGHT = 720
WIKIMEDIA_URL = 'https://upload.wikimedia.org/wikipedia/example.png'


def commons_response() -> dict[str, object]:
    """Return a realistic, complete Wikimedia API image record."""
    return {
        'query': {
            'pages': {
                '1': {
                    'title': 'developer errors',
                    'imageinfo': [
                        {
                            'url': WIKIMEDIA_URL,
                            'mime': 'image/png',
                            'width': IMAGE_WIDTH,
                            'height': IMAGE_HEIGHT,
                            'descriptionurl': 'https://commons.wikimedia.org/wiki/File:Example',
                            'extmetadata': {
                                'LicenseShortName': {'value': 'CC BY-SA 4.0'},
                            },
                        },
                    ],
                },
            },
        },
    }


def test_commons_returns_image_with_provenance(tmp_path: Path) -> None:
    """A Commons result keeps its source and license in the image asset."""
    def fake_http(request: httpx.Request) -> httpx.Response:
        """Simulate only API search and media retrieval."""
        if request.url.host == 'commons.wikimedia.org':
            return httpx.Response(HTTP_OK, json=commons_response())
        return httpx.Response(
            HTTP_OK,
            headers={'content-type': 'image/png'},
            content=b'png',
        )

    with httpx.Client(transport=httpx.MockTransport(fake_http)) as client:
        image = CommonsImageProvider(client).fetch('developer errors', 1, tmp_path)
    assert image.image_path.read_bytes() == b'png'
    assert image.license_name == 'CC BY-SA 4.0'
    assert image.source_url.startswith('https://commons.wikimedia.org/')


def test_commons_rejects_empty_search(tmp_path: Path) -> None:
    """No valid search result must be reported explicitly."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            HTTP_OK, json={'query': {'pages': {}}}
        ),
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='No usable Commons image'),
    ):
        CommonsImageProvider(client).fetch('nothing', 1, tmp_path)
