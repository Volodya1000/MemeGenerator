"""Local image provider for numbered, user-supplied scene images."""

import shutil
from pathlib import Path

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene

IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp')


class LocalImageProvider(ImageProviderProtocol):
    """Copy preselected contextual images without remote requests."""

    def __init__(self, source_dir: Path) -> None:
        """Store the folder of images named after their scene positions."""
        self._source_dir = source_dir

    def fetch(
        self,
        scene: Scene,
        output_dir: Path,
    ) -> ImageAsset:
        """Copy the selected image while recording its local origin."""
        candidates = (
            self._source_dir / f'{scene.order}{suffix}'
            for suffix in IMAGE_SUFFIXES
        )
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise FileNotFoundError(f'Missing local image {scene.order}')
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / source.name
        shutil.copyfile(source, destination)
        return ImageAsset(
            image_path=destination,
            source_url=source.resolve().as_uri(),
            license_name='User-provided',
        )
