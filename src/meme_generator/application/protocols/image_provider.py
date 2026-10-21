"""Port for acquiring one visual context image per scene."""

from pathlib import Path
from typing import Protocol

from meme_generator.domain.image_asset import ImageAsset


class ImageProviderProtocol(Protocol):
    """Retrieve or copy a contextual image and its attribution."""

    def fetch(
        self,
        query: str,
        scene_order: int,
        output_dir: Path,
    ) -> ImageAsset:
        """Return a local image owned by the generation workspace."""
        ...
