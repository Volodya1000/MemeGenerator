"""Bounded download of approved Wikimedia-hosted raster images."""

from pathlib import Path
from urllib.parse import urlparse

import httpx

from meme_generator.infrastructure.commons.models import CommonsImage

MAX_IMAGE_BYTES = 12_000_000
VALID_SUFFIXES = frozenset(('.jpg', '.jpeg', '.png', '.webp'))
TRUSTED_MEDIA_HOSTS = frozenset(
    ('upload.wikimedia.org', 'thumb.wikimedia.org')
)


def validate_image_url(url: str) -> None:
    """Reject redirects and unsafe hosts before requesting media."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in TRUSTED_MEDIA_HOSTS:
        raise ValueError('Only direct HTTPS Wikimedia images are permitted')
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only direct HTTPS Wikimedia images are permitted')


def download_image(
    client: httpx.Client,
    metadata: CommonsImage,
    scene_order: int,
    output_dir: Path,
) -> Path:
    """Stream to disk, rejecting unexpected media and excessive bytes."""
    image_url = metadata.thumburl or metadata.url
    validate_image_url(image_url)
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix not in VALID_SUFFIXES:
        raise ValueError('Image has an unsupported extension')
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f'{scene_order}{suffix}'
    try:
        _write_response(client, image_url, destination)
    except (ValueError, httpx.HTTPError, OSError):
        destination.unlink(missing_ok=True)
        raise
    return destination


def _write_response(client: httpx.Client, url: str, target: Path) -> None:
    """Keep streamed response bytes under the configured ceiling."""
    with client.stream('GET', url, follow_redirects=False) as response:
        response.raise_for_status()
        mime_type = response.headers.get('content-type', '').split(';')[0]
        if mime_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise ValueError('Invalid image response type')
        total = 0
        with target.open('wb') as output_file:
            for fragment in response.iter_bytes():
                total += len(fragment)
                if total > MAX_IMAGE_BYTES:
                    raise ValueError('Image exceeds the download size limit')
                output_file.write(fragment)
