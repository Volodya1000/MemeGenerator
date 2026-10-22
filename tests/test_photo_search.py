"""Integration-style fallback contracts for authentic searched photographs."""

from pathlib import Path

from PIL import Image

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.photo_search import (
    PhotoSearchWithFallback,
)


def scene() -> Scene:
    """Preserve two independently meaningful LLM scene descriptions."""
    return Scene(
        order=1,
        description='Когда купил машину. Она сломалась через два дня',
        image_query='broken car roadside smoke',
        meme_id='real_reaction',
    )


class OfflinePhotoProvider:
    """Supply a real decodable photo without an external HTTP call."""

    def fetch(self, situation: Scene, directory: Path) -> ImageAsset:
        """Return an attributable real image using situation order."""
        destination = directory / f'{situation.order}-photo.png'
        directory.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (1280, 720), 'yellow').save(destination)
        return ImageAsset(
            image_path=destination,
            source_url='https://example.org/real-source',
            license_name='Approved photo',
        )


class MissingPhotoProvider:
    """Represent a genuine empty search response."""

    def fetch(self, situation: Scene, directory: Path) -> ImageAsset:
        """Report no suitable photograph."""
        raise ValueError('No usable photograph found')


class CorruptedPhotoProvider:
    """Represent a downloaded file that is not a decodable photograph."""

    def fetch(self, situation: Scene, directory: Path) -> ImageAsset:
        """Return a misleading image filename with invalid bytes."""
        destination = directory / 'broken.png'
        directory.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b'not an actual photograph')
        return ImageAsset(
            image_path=destination,
            source_url='https://example.org/broken',
            license_name='Invalid image',
        )


def test_photo_search_preserves_original_source(tmp_path: Path) -> None:
    """A successful photo search never substitutes its source attribution."""
    provider = PhotoSearchWithFallback(
        OfflinePhotoProvider(), CaptionCardImageProvider()
    )
    asset = provider.fetch(scene(), tmp_path)
    assert asset.license_name == 'Approved photo'
    with Image.open(asset.image_path) as image:
        assert image.getpixel((100, 100)) == (255, 255, 0)


def test_missing_photo_falls_back_to_scene_text(tmp_path: Path) -> None:
    """Unsuccessful search produces readable original-situation typography."""
    provider = PhotoSearchWithFallback(
        MissingPhotoProvider(), CaptionCardImageProvider()
    )
    asset = provider.fetch(scene(), tmp_path)
    assert asset.license_name == 'Original generated typography'
    with Image.open(asset.image_path) as image:
        assert image.size == (1280, 720)


def test_corrupted_photo_never_enters_ffmpeg(tmp_path: Path) -> None:
    """A broken image download cannot become a broken video artifact."""
    provider = PhotoSearchWithFallback(
        CorruptedPhotoProvider(), CaptionCardImageProvider()
    )
    asset = provider.fetch(scene(), tmp_path)
    with Image.open(asset.image_path) as image:
        image.verify()
