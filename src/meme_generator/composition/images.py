"""Compose selected visual providers at the application boundary."""

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.slide_mode import SlideMode
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.captioned_images import (
    CaptionedImageProvider,
)
from meme_generator.infrastructure.commons import CommonsImageProvider
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.pexels.provider import PexelsImageProvider
from meme_generator.infrastructure.photo_search import PhotoSearchWithFallback
from meme_generator.infrastructure.unsplash.provider import UnsplashImageProvider


def _photo_source(settings: GenerationSettings) -> ImageProviderProtocol:
    """Try Unsplash first, then optional Pexels and finally Commons."""
    commons: ImageProviderProtocol = CommonsImageProvider()
    photo: ImageProviderProtocol = commons
    pexels_key = settings.pexels.api_key
    if pexels_key is not None and pexels_key.get_secret_value().strip():
        photo = PhotoSearchWithFallback(
            PexelsImageProvider(settings.pexels), photo
        )
    unsplash_key = settings.unsplash.access_key
    if unsplash_key is not None and unsplash_key.get_secret_value().strip():
        photo = PhotoSearchWithFallback(
            UnsplashImageProvider(settings.unsplash), photo
        )
    return photo


def _configured_photo(settings: GenerationSettings) -> ImageProviderProtocol:
    """Resolve the requested photo source, retaining the local mode."""
    if settings.images == 'photos':
        return _photo_source(settings)
    if settings.images == 'commons':
        return CommonsImageProvider()
    if settings.image_dir is None:
        raise ValueError('image_dir is required when images=local')
    return LocalImageProvider(settings.image_dir.resolve())


def create_images(settings: GenerationSettings) -> ImageProviderProtocol:
    """Select text cards, genuine pictures, or pictures with captions."""
    if settings.slide_mode == SlideMode.TEXT_ONLY:
        return CaptionCardImageProvider()
    if settings.images == 'cards':
        raise ValueError('Choose commons or local for image slide modes')
    photo = _configured_photo(settings)
    if settings.slide_mode == SlideMode.IMAGE_WITH_CAPTION:
        photo = CaptionedImageProvider(photo)
    if settings.images == 'photos':
        return PhotoSearchWithFallback(photo, CaptionCardImageProvider())
    return photo
