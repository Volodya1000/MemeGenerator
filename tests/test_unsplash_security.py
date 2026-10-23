"""Security contract for remote Unsplash search and selection."""

from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from meme_generator.config.unsplash import UnsplashSettings
from meme_generator.infrastructure.unsplash.provider import (
    UnsplashImageProvider,
)
from tests.test_unsplash_provider import TEST_KEY, example_scene, search_response

HTTP_OK = 200


def test_untrusted_tracking_url_is_rejected(tmp_path: Path) -> None:
    """Never send Client-ID to URLs outside the fixed API host."""
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            HTTP_OK,
            json=search_response('https://evil.example/download'),
        )
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='Untrusted Unsplash'),
    ):
        UnsplashImageProvider(
            UnsplashSettings(access_key=SecretStr(TEST_KEY)), client
        ).fetch(example_scene(), tmp_path)
    assert not list(tmp_path.iterdir())
