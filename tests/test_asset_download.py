"""Fail-safe media download validation without external HTTP calls."""

from pathlib import Path

import httpx
import pytest
from pydantic import HttpUrl, TypeAdapter

from meme_generator.infrastructure.assets import download

URL = 'https://media.example.org/reaction.mp4'
REQUEST = httpx.Request('GET', URL)


@pytest.mark.parametrize(
    'raw_url',
    [
        'http://media.example.org/reaction.mp4',
        'https://localhost/reaction.mp4',
        'https://127.0.0.1/reaction.mp4',
        'https://user:secret@media.example.org/reaction.mp4',
    ],
)
def test_unsafe_media_hosts_are_rejected(raw_url: str, tmp_path: Path) -> None:
    """Invalid URL schemes or hosts fail before any network I/O."""
    url = TypeAdapter(HttpUrl).validate_python(raw_url)
    with pytest.raises(ValueError):
        download.download_media(url, tmp_path / 'media.mp4')


def test_streamed_response_is_saved(tmp_path: Path) -> None:
    """The successful response writes the expected bytes to local disk."""
    destination = tmp_path / 'source.mp4'
    response = httpx.Response(200, content=b'mp4', request=REQUEST)
    download._save_response(response, destination)
    assert destination.read_bytes() == b'mp4'


def test_empty_download_is_rejected(tmp_path: Path) -> None:
    """No downloaded bytes can be treated as a usable reaction."""
    response = httpx.Response(200, content=b'', request=REQUEST)
    with pytest.raises(ValueError, match='empty'):
        download._save_response(response, tmp_path / 'source.mp4')


def test_oversized_download_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bounded media downloads stop at the configured byte limit."""
    monkeypatch.setattr(download, 'MAX_MEDIA_BYTES', 2)
    response = httpx.Response(200, content=b'mp4', request=REQUEST)
    with pytest.raises(ValueError, match='50 MiB'):
        download._save_response(response, tmp_path / 'source.mp4')


def test_http_error_is_not_written(tmp_path: Path) -> None:
    """An HTTP failure cannot create a successful media payload."""
    response = httpx.Response(404, request=REQUEST)
    target = tmp_path / 'source.mp4'
    with pytest.raises(httpx.HTTPStatusError):
        download._save_response(response, target)
    assert not target.exists()
