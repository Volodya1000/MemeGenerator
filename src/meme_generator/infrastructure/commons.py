"""Download relevant Wikimedia Commons images with provenance."""

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.infrastructure.images import IMAGE_SUFFIXES

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 360
MAX_IMAGE_BYTES = 12_000_000
HTTP_TIMEOUT_SECONDS = 30


def search_parameters(query: str) -> dict[str, str | int]:
    """Limit Commons search results to sufficiently descriptive files."""
    return {
        'action': 'query',
        'format': 'json',
        'generator': 'search',
        'gsrsearch': query,
        'gsrnamespace': 6,
        'gsrlimit': 15,
        'prop': 'imageinfo',
        'iiprop': 'url|size|mime|extmetadata',
        'iiurlwidth': 1280,
    }


def is_usable(page: dict[str, Any]) -> bool:
    """Skip files without a sufficiently large raster image stream."""
    images = page.get('imageinfo', [])
    if not images:
        return False
    metadata = images[0]
    return bool(
        metadata.get('mime', '').startswith('image/')
        and metadata.get('width', 0) >= MIN_IMAGE_WIDTH
        and metadata.get('height', 0) >= MIN_IMAGE_HEIGHT
    )


def choose_page(
    pages: list[dict[str, Any]],
    query: str,
) -> dict[str, Any]:
    """Rank usable images by overlap with the requested situation."""
    relevant = [page for page in pages if is_usable(page)]
    if not relevant:
        raise ValueError('No usable Commons image found')
    query_words = set(query.lower().split())
    ranked = sorted(
        relevant,
        key=lambda page: len(
            query_words.intersection(
                set(page['title'].lower().replace('_', ' ').split()),
            ),
        ),
        reverse=True,
    )
    return ranked[0]


def validate_image_url(url: str) -> None:
    """Prevent SSRF through external or non-HTTPS media URLs."""
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        raise ValueError('Only HTTPS images are permitted')
    if parsed.hostname != 'upload.wikimedia.org':
        raise ValueError('Only Wikimedia-hosted images are permitted')


def download_image(
    client: httpx.Client,
    metadata: dict[str, Any],
    scene_order: int,
    output_dir: Path,
) -> Path:
    """Download one strictly size-limited Wikimedia-hosted image."""
    image_url = metadata.get('thumburl', metadata['url'])
    validate_image_url(image_url)
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError('Image has an unsupported extension')
    response = client.get(image_url, follow_redirects=False)
    response.raise_for_status()
    if len(response.content) > MAX_IMAGE_BYTES:
        raise ValueError('Image exceeds the download size limit')
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f'{scene_order}{suffix}'
    destination.write_bytes(response.content)
    return destination


class CommonsImageProvider:
    """Wikimedia Commons image search with a deterministic title ranking."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Allow dependency injection for API tests."""
        self._client = client or httpx.Client(timeout=HTTP_TIMEOUT_SECONDS)

    def fetch(
        self,
        query: str,
        scene_order: int,
        output_dir: Path,
    ) -> ImageAsset:
        """Save an image with Commons attribution for later auditing."""
        response = self._client.get(
            COMMONS_API,
            params=search_parameters(query),
        )
        response.raise_for_status()
        pages = response.json().get('query', {}).get('pages', {})
        metadata = choose_page(list(pages.values()), query)['imageinfo'][0]
        image_path = download_image(
            self._client,
            metadata,
            scene_order,
            output_dir,
        )
        license_metadata = metadata.get('extmetadata', {})
        return ImageAsset(
            image_path=image_path,
            source_url=metadata.get('descriptionurl', metadata['url']),
            license_name=license_metadata.get(
                'LicenseShortName',
                {},
            ).get('value', 'Wikimedia Commons'),
        )
