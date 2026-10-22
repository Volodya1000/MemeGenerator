"""Offline Pexels contract tests using a real HTTP boundary mock."""

from io import BytesIO
from pathlib import Path

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from meme_generator.config.pexels import PexelsSettings
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.pexels.provider import (
    PexelsImageProvider,
)

HTTP_OK = 200
HTTP_UNAVAILABLE = 503
IMAGE_SIZE = (1280, 720)


def example_scene() -> Scene:
    """Describe one scene while keeping the image query independent."""
    return Scene(
        order=1,
        description='Машина сломалась',
        image_query='broken car',
        meme_id='reaction',
    )


def image_data() -> bytes:
    """Generate genuine JPEG bytes for verification without the internet."""
    output = BytesIO()
    Image.new('RGB', IMAGE_SIZE, 'red').save(output, format='JPEG')
    return output.getvalue()


def search_result(image_url: str) -> dict[str, object]:
    """Return a Pexels-style photograph with attribution metadata."""
    return {
        'photos': [
            {
                'width': IMAGE_SIZE[0],
                'height': IMAGE_SIZE[1],
                'url': 'https://www.pexels.com/photo/car-123/',
                'photographer': 'Test Photographer',
                'photographer_url': 'https://www.pexels.com/@photographer',
                'src': {'landscape': image_url},
            },
        ],
    }


def test_search_preserves_photo_and_credit(tmp_path: Path) -> None:
    """An authenticated query returns real media with an author credit."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Observe the API call and serve a JPEG from the Pexels CDN."""
        requests.append(request)
        if request.url.host == 'api.pexels.com':
            return httpx.Response(
                HTTP_OK,
                json=search_result('https://images.pexels.com/car.jpeg'),
            )
        return httpx.Response(
            HTTP_OK,
            content=image_data(),
            headers={'content-type': 'image/jpeg'},
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = PexelsImageProvider(
            PexelsSettings(api_key=SecretStr('offline-key')), client
        )
        photo = provider.fetch(example_scene(), tmp_path)
    with Image.open(photo.image_path) as decoded:
        decoded.verify()
    assert 'Test Photographer' in photo.license_name
    assert photo.source_url.startswith('https://www.pexels.com/')
    assert requests[0].headers.get('authorization') == 'offline-key'
    assert 'authorization' not in requests[1].headers
    assert requests[0].url.params['orientation'] == 'landscape'


def test_empty_search_rejects_missing_photos(tmp_path: Path) -> None:
    """An empty Pexels response permits fallback to Commons."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(HTTP_OK, json={'photos': []})
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='No usable Pexels'),
    ):
        PexelsImageProvider(
            PexelsSettings(api_key=SecretStr('offline-key')), client
        ).fetch(example_scene(), tmp_path)


def test_missing_key_is_rejected() -> None:
    """The adapter cannot silently use the Pexels API anonymously."""
    with pytest.raises(ValueError, match='API key'):
        PexelsImageProvider(PexelsSettings())


def test_http_error_propagates_for_fallback(tmp_path: Path) -> None:
    """An unavailable Pexels service raises a bounded HTTP error."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(HTTP_UNAVAILABLE)
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        PexelsImageProvider(
            PexelsSettings(api_key=SecretStr('offline-key')), client
        ).fetch(example_scene(), tmp_path)
