"""Pexels search adapter with explicit provenance and bounded downloads."""

from pathlib import Path

import httpx

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.config.pexels import PexelsSettings
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.pexels.download import download_photo
from meme_generator.infrastructure.pexels.models import (
    PexelsPhoto,
    PexelsResponse,
)
from meme_generator.infrastructure.pexels.search import (
    PEXELS_SEARCH_URL,
    choose_photo,
    search_parameters,
)


class PexelsImageProvider(ImageProviderProtocol):
    """Search ranked Pexels photos before the outer Commons fallback."""

    def __init__(
        self,
        settings: PexelsSettings,
        client: httpx.Client | None = None,
    ) -> None:
        """Authenticate without ever putting the secret in query params."""
        if settings.api_key is None:
            raise ValueError('Pexels requires an API key')
        self._settings = settings
        self._api_key = settings.api_key
        self._client = client or httpx.Client(
            timeout=settings.timeout_seconds,
        )

    def fetch(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Retrieve an attributable photograph for one planned scene."""
        photo = self._search(scene.image_query)
        destination = download_photo(
            self._client, photo.src.landscape, scene.order, output_dir
        )
        return ImageAsset(
            image_path=destination,
            source_url=str(photo.url),
            license_name=(
                f'Pexels License; Photo by {photo.photographer} on Pexels '
                f'({photo.photographer_url})'
            ),
        )

    def _search(self, query: str) -> PexelsPhoto:
        """Validate an untrusted search response before selecting a photo."""
        response = self._client.get(
            PEXELS_SEARCH_URL,
            params=search_parameters(query, self._settings),
            headers={'Authorization': self._api_key.get_secret_value()},
        )
        response.raise_for_status()
        photos = PexelsResponse.model_validate(response.json()).photos
        return choose_photo(photos)
