"""Optional bounded download of explicitly configured public media."""

import ipaddress
import tempfile
from pathlib import Path

import httpx
from pydantic import HttpUrl

from meme_generator.infrastructure.assets.probe import (
    MAX_MEDIA_BYTES,
    check_source,
)

DOWNLOAD_TIMEOUT_SECONDS = 30


def _validate_media_url(url: HttpUrl) -> None:
    """Avoid local hosts, IP literals, credentials, and insecure protocols."""
    host = url.host or ''
    if url.scheme != 'https' or url.username or not host:
        raise ValueError('Media URL must use public HTTPS without credentials')
    if host == 'localhost' or host.endswith('.localhost'):
        raise ValueError('Media URL must not point to localhost')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return
    raise ValueError('Media URL must not contain a literal IP address')


def save_download_response(response: httpx.Response, path: Path) -> None:
    """Save a successful download with a strict maximum size."""
    response.raise_for_status()
    downloaded = 0
    with path.open('wb') as output:
        for chunk in response.iter_bytes():
            downloaded += len(chunk)
            if downloaded > MAX_MEDIA_BYTES:
                raise ValueError('Download exceeds the 50 MiB limit')
            output.write(chunk)
    if not downloaded:
        raise ValueError('Downloaded media is empty')


def download_media(url: HttpUrl, destination: Path) -> None:
    """Fetch a direct HTTPS video without redirects or scraping."""
    _validate_media_url(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        temporary = Path(directory) / 'source.mp4'
        with (
            httpx.Client(
                follow_redirects=False,
                timeout=DOWNLOAD_TIMEOUT_SECONDS,
            ) as client,
            client.stream('GET', str(url)) as response,
        ):
            save_download_response(response, temporary)
        check_source(temporary, None)
        temporary.replace(destination)
