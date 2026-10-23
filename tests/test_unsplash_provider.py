"""Offline Unsplash API contract and credential-leakage tests."""

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from meme_generator.config.unsplash import UnsplashSettings
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.unsplash.provider import (
    UnsplashImageProvider,
)

HTTP_OK = 200
HTTP_UNAVAILABLE = 503
FRAME_SIZE = (1280, 720)
TEST_KEY = 'test-unsplash-access-key'


def example_scene() -> Scene:
    """Provide a minimal valid scene for integration tests."""
    return Scene(
        order=1,
        description='Машина сломалась',
        image_query='broken car',
        meme_id='reaction',
    )


def search_response(
    tracking_url: str = (
        'https://api.unsplash.com/photos/phototest/download?ixid=123'
    ),
) -> dict[str, object]:
    """Return the Unsplash fields required to download and credit a photo."""
    return {
        'results': [{
            'id': 'phototest',
            'width': FRAME_SIZE[0],
            'height': FRAME_SIZE[1],
            'urls': {'regular': 'https://images.unsplash.com/car.jpg'},
            'links': {
                'html': 'https://unsplash.com/photos/phototest',
                'download_location': tracking_url,
            },
            'user': {
                'name': 'Sample Author',
                'links': {'html': 'https://unsplash.com/@sample'},
            },
        }],
    }


def mock_api(request: httpx.Request) -> httpx.Response:
    """Exercise search, image transfer and tracking across both hosts."""
    if request.url.host == 'images.unsplash.com':
        assert 'authorization' not in request.headers
        encoded_photo = BytesIO()
        Image.new('RGB', FRAME_SIZE, 'red').save(
            encoded_photo, format='JPEG'
        )
        return httpx.Response(
            HTTP_OK, content=encoded_photo.getvalue(),
            headers={'content-type': 'image/jpeg'},
        )
    assert request.headers.get('authorization') == f'Client-ID {TEST_KEY}'
    if request.url.path.endswith('/download'):
        assert request.url.params['ixid'] == '123'
        return httpx.Response(HTTP_OK, json={'url': 'https://example.com'})
    assert request.url.params['orientation'] == 'landscape'
    return httpx.Response(HTTP_OK, json=search_response())


def test_real_photo_and_download_tracking(tmp_path: Path) -> None:
    """Download a JPEG once and send the required download counter call."""
    handler: Mock = Mock(wraps=mock_api)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = UnsplashImageProvider(
            UnsplashSettings(access_key=SecretStr(TEST_KEY)), client
        )
        image = provider.fetch(example_scene(), tmp_path)
    assert handler.call_count == 3
    assert '/download' in str(handler.call_args_list[-1].args[0].url)
    assert 'Sample Author' in image.license_name
    assert 'utm_source=MemeGenerator' in image.source_url
    with Image.open(image.image_path) as photo:
        photo.verify()


def test_unavailable_search_uses_fallback(
    tmp_path: Path,
) -> None:
    """An Unsplash outage propagates to the existing fallback adapter."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(HTTP_UNAVAILABLE)
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        UnsplashImageProvider(
            UnsplashSettings(access_key=SecretStr(TEST_KEY)), client
        ).fetch(example_scene(), tmp_path)


def test_missing_key_fails_closed() -> None:
    """Do not issue anonymous or accidentally credentialed requests."""
    with pytest.raises(ValueError, match='access key'):
        UnsplashImageProvider(UnsplashSettings())


def test_empty_search_can_fall_back(tmp_path: Path) -> None:
    """An empty result is a recoverable search error."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(HTTP_OK, json={'results': []})
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='No usable Unsplash'),
    ):
        UnsplashImageProvider(
            UnsplashSettings(access_key=SecretStr(TEST_KEY)), client
        ).fetch(example_scene(), tmp_path)
