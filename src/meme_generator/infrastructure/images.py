"""Local contextual image provider and common image source contracts."""

import shutil
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel

IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp')


class ImageAsset(BaseModel):
    """Local image plus source and licensing metadata."""

    image_path: Path
    source_url: str
    license_name: str


class ImageProvider(Protocol):
    """Interchangeable source for contextual scene pictures."""

    def fetch(
        self,
        query: str,
        scene_order: int,
        output_dir: Path,
    ) -> ImageAsset:
        """Supply one scene image with its provenance."""
        ...


class LocalImageProvider:
    """Use numbered local scene images, never random online content."""

    def __init__(self, source_dir: Path) -> None:
        """Store the root folder of preselected pictures."""
        self._source_dir = source_dir

    def fetch(
        self,
        query: str,
        scene_order: int,
        output_dir: Path,
    ) -> ImageAsset:
        """Copy exactly the supplied image with the matching scene number."""
        candidates = (
            self._source_dir / f'{scene_order}{suffix}'
            for suffix in IMAGE_SUFFIXES
        )
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise FileNotFoundError(f'Missing local image {scene_order}')
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / source.name
        shutil.copyfile(source, destination)
        return ImageAsset(
            image_path=destination,
            source_url=source.as_uri(),
            license_name='User-provided',
        )
