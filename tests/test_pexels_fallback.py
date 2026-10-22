"""Integration contracts for Pexels-to-Commons-to-card recovery."""

from pathlib import Path

import httpx
from PIL import Image
from pydantic import SecretStr

from meme_generator.config.pexels import PexelsSettings
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.pexels.provider import (
    PexelsImageProvider,
)
from meme_generator.infrastructure.photo_search import (
    PhotoSearchWithFallback,
)

HTTP_UNAVAILABLE = 503
FRAME_SIZE = (1280, 720)


def example_scene() -> Scene:
    """Use one meaningful Russian caption and an English photo query."""
    return Scene(
        order=1,
        description='Машина сломалась на дороге',
        image_query='broken car',
        meme_id='reaction',
    )


class OfflineCommonsProvider:
    """Provide a verifiable Commons-like photo without a network call."""

    def fetch(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Keep attribution intact when falling back to Commons."""
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / f'{scene.order}-commons.png'
        Image.new('RGB', FRAME_SIZE, 'blue').save(destination)
        return ImageAsset(
            image_path=destination,
            source_url='https://commons.wikimedia.org/wiki/File:Car',
            license_name='CC BY 4.0',
        )


def test_pexels_unavailable_uses_commons(tmp_path: Path) -> None:
    """A Pexels outage cannot prevent a genuine Commons photograph."""
    transport = httpx.MockTransport(lambda _: httpx.Response(HTTP_UNAVAILABLE))
    with httpx.Client(transport=transport) as client:
        provider = PhotoSearchWithFallback(
            PexelsImageProvider(
                PexelsSettings(api_key=SecretStr('offline-key')), client
            ),
            OfflineCommonsProvider(),
        )
        photo = provider.fetch(example_scene(), tmp_path)
    assert photo.license_name == 'CC BY 4.0'
    with Image.open(photo.image_path) as decoded:
        decoded.verify()


def test_no_photo_service_uses_readable_card(tmp_path: Path) -> None:
    """A missing source still yields a readable locally rendered card."""
    transport = httpx.MockTransport(lambda _: httpx.Response(HTTP_UNAVAILABLE))
    with httpx.Client(transport=transport) as client:
        commons = PhotoSearchWithFallback(
            PexelsImageProvider(
                PexelsSettings(api_key=SecretStr('offline-key')), client
            ),
            CaptionCardImageProvider(),
        )
        asset = commons.fetch(example_scene(), tmp_path)
    assert asset.license_name == 'Original generated typography'
    with Image.open(asset.image_path) as decoded:
        decoded.verify()
