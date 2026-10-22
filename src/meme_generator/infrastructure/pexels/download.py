"""Bounded HTTPS download restricted to the official Pexels image CDN."""

from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import HttpUrl

MAX_IMAGE_BYTES = 12_000_000
PEXELS_IMAGE_HOST = 'images.pexels.com'
MIME_JPEG = 'image/jpeg'


def validate_photo_url(url: str) -> None:
    """Prevent untrusted API payloads from requesting arbitrary addresses."""
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != PEXELS_IMAGE_HOST:
        raise ValueError('Only HTTPS Pexels photo URLs are permitted')
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only HTTPS Pexels photo URLs are permitted')


def download_photo(
    client: httpx.Client,
    source: HttpUrl,
    scene_order: int,
    output_dir: Path,
) -> Path:
    """Download one JPEG with a byte ceiling and automatic error cleanup."""
    image_url = str(source)
    validate_photo_url(image_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f'{scene_order}-pexels.jpg'
    try:
        _write_photo(client, image_url, destination)
    except (OSError, ValueError, httpx.HTTPError):
        destination.unlink(missing_ok=True)
        raise
    return destination


def _write_photo(
    client: httpx.Client,
    image_url: str,
    destination: Path,
) -> None:
    """Reject redirects, non-image payloads and oversized image bodies."""
    with client.stream('GET', image_url, follow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError('Pexels photo redirects are not permitted')
        mime_type = response.headers.get('content-type', '').split(';')[0]
        if mime_type != MIME_JPEG:
            raise ValueError('Pexels response is not a JPEG photograph')
        total = 0
        with destination.open('wb') as output_file:
            for fragment in response.iter_bytes():
                total += len(fragment)
                if total > MAX_IMAGE_BYTES:
                    raise ValueError('Pexels photo exceeds the byte limit')
                output_file.write(fragment)
