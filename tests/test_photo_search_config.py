"""Selection contract for the automatic real-photo search source."""

from pydantic import SecretStr

from meme_generator.composition.images import create_images
from meme_generator.config.pexels import PexelsSettings
from meme_generator.config.unsplash import UnsplashSettings

PHOTO_MODE = 'photos'
from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.slide_mode import SlideMode
from meme_generator.infrastructure.photo_search import (
    PhotoSearchWithFallback,
)


def test_photo_search_needs_no_new_api_key() -> None:
    """Wikimedia search runs with no further user credentials."""
    provider = create_images(
        GenerationSettings(
            slide_mode=SlideMode.IMAGE_ONLY,
            images=PHOTO_MODE,
        )
    )
    assert isinstance(provider, PhotoSearchWithFallback)


def test_pexels_key_keeps_existing_photo_fallback() -> None:
    """Adding credentials keeps the normal photo-mode fallback enabled."""
    provider = create_images(
        GenerationSettings(
            slide_mode=SlideMode.IMAGE_WITH_CAPTION,
            images=PHOTO_MODE,
            pexels=PexelsSettings(api_key=SecretStr('offline-key')),
        )
    )
    assert isinstance(provider, PhotoSearchWithFallback)


def test_empty_optional_key_uses_commons() -> None:
    """A missing GitHub secret stays equivalent to an absent API key."""
    provider = create_images(
        GenerationSettings(
            slide_mode=SlideMode.IMAGE_ONLY,
            images=PHOTO_MODE,
            pexels=PexelsSettings(api_key=SecretStr('')),
        )
    )
    assert isinstance(provider, PhotoSearchWithFallback)


def test_unsplash_key_keeps_existing_fallback() -> None:
    """Adding an Unsplash key preserves the Commons and caption fallback."""
    provider = create_images(
        GenerationSettings(
            slide_mode=SlideMode.IMAGE_WITH_CAPTION,
            images=PHOTO_MODE,
            unsplash=UnsplashSettings(access_key=SecretStr('offline-key')),
        )
    )
    assert isinstance(provider, PhotoSearchWithFallback)
