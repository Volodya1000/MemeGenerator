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


def create_images(settings: GenerationSettings) -> ImageProviderProtocol:
    """Select text cards, genuine pictures, or pictures with captions."""
    if settings.slide_mode == SlideMode.TEXT_ONLY:
        return CaptionCardImageProvider()
    if settings.images == 'cards':
        raise ValueError('Choose commons or local for image slide modes')
    if settings.images == 'commons':
        photo: ImageProviderProtocol = CommonsImageProvider()
    else:
        if settings.image_dir is None:
            raise ValueError('image_dir is required when images=local')
        photo = LocalImageProvider(settings.image_dir.resolve())
    if settings.slide_mode == SlideMode.IMAGE_WITH_CAPTION:
        return CaptionedImageProvider(photo)
    return photo
