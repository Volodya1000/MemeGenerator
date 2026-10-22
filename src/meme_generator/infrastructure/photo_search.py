"""Recover from missing online photographs with a readable situation card."""

import logging
from pathlib import Path

import httpx
from PIL import Image, UnidentifiedImageError

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene

LOGGER = logging.getLogger(__name__)
PHOTO_FAILURES = (
    httpx.HTTPError,
    ValueError,
    OSError,
    UnidentifiedImageError,
)


class PhotoSearchWithFallback(ImageProviderProtocol):
    """Try searchable real photographs, then show the original scene text."""

    def __init__(
        self,
        primary: ImageProviderProtocol,
        fallback: ImageProviderProtocol,
    ) -> None:
        """Supply both providers without hidden global dependencies."""
        self._primary = primary
        self._fallback = fallback

    def fetch(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Do not publish missing, unreadable or unrelated file content."""
        try:
            photo = self._validated_photo(scene, output_dir)
        except PHOTO_FAILURES as failure:
            LOGGER.warning(
                'PHOTO_UNAVAILABLE scene=%s failure=%s: %s',
                scene.order,
                type(failure).__name__,
                failure,
            )
            return self._fallback.fetch(scene, output_dir)
        return photo

    def _validated_photo(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Return a decoded real photo or raise a bounded media error."""
        photo = self._primary.fetch(scene, output_dir)
        with Image.open(photo.image_path) as image:
            image.verify()
        return photo
