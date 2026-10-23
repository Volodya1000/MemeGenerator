"""Stream Unsplash JPEG from its CDN with strict URL and size validation."""

from pathlib import Path
from urllib.parse import urlsplit

import httpx
from pydantic import HttpUrl

MAX_IMAGE_BYTES = 12_000_000
IMAGE_CDN_HOST = 'images.unsplash.com'
API_HOST = 'api.unsplash.com'
MIME_JPEG = 'image/jpeg'


def _require_https_host(url: str, hostname: str) -> None:
    """Reject external hosts, credentials, insecure URLs and unusual ports."""
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname != hostname:
        raise ValueError('Untrusted Unsplash URL')
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Untrusted Unsplash URL')


def validate_download_location(url: HttpUrl, photo_id: str) -> None:
    """Prevent an API response from redirecting authenticated requests."""
    raw = str(url)
    _require_https_host(raw, API_HOST)
    if urlsplit(raw).path != f'/photos/{photo_id}/download':
        raise ValueError('Untrusted Unsplash download tracking URL')


def download_photo(
    client: httpx.Client,
    source: HttpUrl,
    scene_order: int,
    output_dir: Path,
) -> Path:
    """Save the original returned CDN URL without following redirects."""
    image_url = str(source)
    _require_https_host(image_url, IMAGE_CDN_HOST)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f'{scene_order}-unsplash.jpg'
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
    """Reject redirects, invalid MIME and oversized responses."""
    with client.stream('GET', image_url, follow_redirects=False) as response:
        if response.is_redirect:
            raise ValueError('Unsplash image redirects are not allowed')
        response.raise_for_status()
        mime_type = response.headers.get('content-type', '').split(';')[0]
        if mime_type != MIME_JPEG:
            raise ValueError('Unsplash response must be JPEG')
        total: int = 0
        with destination.open('wb') as output_file:
            for fragment in response.iter_bytes():
                total += len(fragment)
                if total > MAX_IMAGE_BYTES:
                    raise ValueError('Unsplash photo exceeds byte limit')
                output_file.write(fragment)
