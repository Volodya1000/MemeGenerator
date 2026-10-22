"""Selection contract for the automatic real-photo search source."""

from meme_generator.composition.images import create_images
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
            images='photos',
        )
    )
    assert isinstance(provider, PhotoSearchWithFallback)
