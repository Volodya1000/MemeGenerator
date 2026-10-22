"""Wikimedia Commons adapter that preserves image provenance."""

from pathlib import Path

import httpx

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.commons.download import download_image
from meme_generator.infrastructure.commons.models import (
    CommonsImage,
    CommonsResponse,
)
from meme_generator.infrastructure.commons.search import (
    COMMONS_API,
    choose_page,
    search_parameters,
)

HTTP_TIMEOUT_SECONDS = 30
WIKIMEDIA_USER_AGENT = (
    'MemeGenerator/0.1 (https://github.com/Volodya1000/MemeGenerator)'
)


class CommonsImageProvider(ImageProviderProtocol):
    """Find, download, and attribute contextual Commons images."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Allow offline HTTP transport injection at the service boundary."""
        self._client = client or httpx.Client(
            timeout=HTTP_TIMEOUT_SECONDS,
            headers={'User-Agent': WIKIMEDIA_USER_AGENT},
        )

    def fetch(
        self,
        scene: Scene,
        output_dir: Path,
    ) -> ImageAsset:
        """Select and return one locally downloaded, attributed image."""
        metadata = self._search_metadata(scene.image_query)
        image_path = download_image(
            self._client, metadata, scene.order, output_dir
        )
        license_entry = metadata.extmetadata.get('LicenseShortName')
        license_name = (
            str(license_entry.value)
            if license_entry
            else 'Wikimedia Commons'
        )
        return ImageAsset(
            image_path=image_path,
            source_url=metadata.descriptionurl or metadata.url,
            license_name=license_name,
        )

    def _search_metadata(self, query: str) -> CommonsImage:
        """Validate the API response and choose a usable Commons image."""
        response = self._client.get(
            COMMONS_API,
            params=search_parameters(query),
        )
        response.raise_for_status()
        catalog = CommonsResponse.model_validate(response.json())
        selected = choose_page(list(catalog.query.pages.values()), query)
        return selected.imageinfo[0]
