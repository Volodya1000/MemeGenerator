"""Unsplash authenticated photo search with required download tracking."""

from pathlib import Path

import httpx
from PIL import Image

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.config.unsplash import UnsplashSettings
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.unsplash.download import (
    download_photo,
    validate_download_location,
)
from meme_generator.infrastructure.unsplash.models import (
    UnsplashPhoto,
    UnsplashResponse,
)
from meme_generator.infrastructure.unsplash.search import (
    UNSPLASH_SEARCH_URL,
    choose_photo,
    search_parameters,
)

UTM_PARAMETERS = 'utm_source=MemeGenerator&utm_medium=referral'


def _attributed_url(url: str) -> str:
    """Add the referral markers required by the provider guidelines."""
    separator = '&' if '?' in url else '?'
    return f'{url}{separator}{UTM_PARAMETERS}'


class UnsplashImageProvider(ImageProviderProtocol):
    """Search and download images without exposing an Unsplash access key."""

    def __init__(
        self,
        settings: UnsplashSettings,
        client: httpx.Client | None = None,
    ) -> None:
        """Support a mocked transport for deterministic offline tests."""
        key = settings.access_key
        if key is None or not key.get_secret_value().strip():
            raise ValueError('Unsplash requires an access key')
        self._settings = settings
        self._authorization = f'Client-ID {key.get_secret_value()}'
        self._client = client or httpx.Client(timeout=settings.timeout_seconds)

    def fetch(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Download one photo and register the real image selection."""
        photo = self._search(scene.image_query)
        validate_download_location(photo.links.download_location, photo.id)
        destination = download_photo(
            self._client, photo.urls.regular, scene.order, output_dir
        )
        try:
            self._validate_and_track(photo, destination)
        except (OSError, ValueError, httpx.HTTPError):
            destination.unlink(missing_ok=True)
            raise
        photographer: str = _attributed_url(str(photo.user.links.html))
        author: str = photo.user.name
        return ImageAsset(
            image_path=destination,
            source_url=_attributed_url(str(photo.links.html)),
            license_name=(
                f'Unsplash License; Photo by {author} on Unsplash '
                f'({photographer})'
            ),
        )

    def _search(self, query: str) -> UnsplashPhoto:
        """Search using public Client-ID auth scoped to the Unsplash API."""
        response = self._client.get(
            UNSPLASH_SEARCH_URL,
            params=search_parameters(query, self._settings),
            headers={'Authorization': self._authorization},
            follow_redirects=False,
        )
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('Unexpected Unsplash search redirect')
        photos = UnsplashResponse.model_validate(response.json()).photos
        return choose_photo(photos)

    def _validate_and_track(
        self,
        photo: UnsplashPhoto,
        destination: Path,
    ) -> None:
        """Reject invalid JPEG bytes before counting a completed download."""
        with Image.open(destination) as decoded:
            decoded.verify()
        self._track_download(photo)

    def _track_download(self, photo: UnsplashPhoto) -> None:
        """Record the required download event for a selected photograph."""
        response = self._client.get(
            str(photo.links.download_location),
            headers={'Authorization': self._authorization},
            follow_redirects=False,
        )
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('Unexpected Unsplash tracking redirect')
