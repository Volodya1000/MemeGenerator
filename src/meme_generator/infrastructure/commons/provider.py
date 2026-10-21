"""Wikimedia Commons adapter that preserves image provenance."""

from pathlib import Path

import httpx

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.infrastructure.commons.download import download_image
from meme_generator.infrastructure.commons.models import CommonsResponse
from meme_generator.infrastructure.commons.search import (
    COMMONS_API,
    choose_page,
    search_parameters,
)

HTTP_TIMEOUT_SECONDS = 30


class CommonsImageProvider:
    """Find, download, and attribute contextual Commons images."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Allow offline HTTP transport injection at the service boundary."""
        self._client = client or httpx.Client(timeout=HTTP_TIMEOUT_SECONDS)

    def fetch(
        self,
        query: str,
        scene_order: int,
        output_dir: Path,
    ) -> ImageAsset:
        """Select and return one locally downloaded, attributed image."""
        response = self._client.get(
            COMMONS_API,
            params=search_parameters(query),
        )
        response.raise_for_status()
        catalog = CommonsResponse.model_validate(response.json())
        selected = choose_page(list(catalog.query.pages.values()), query)
        metadata = selected.imageinfo[0]
        image_path = download_image(
            self._client, metadata, scene_order, output_dir
        )
        license_entry = metadata.extmetadata.get('LicenseShortName')
        license_name = (
            license_entry.value if license_entry else 'Wikimedia Commons'
        )
        return ImageAsset(
            image_path=image_path,
            source_url=metadata.descriptionurl or metadata.url,
            license_name=license_name,
        )
