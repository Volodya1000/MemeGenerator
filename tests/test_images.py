"""Image providers must not guess a missing local scene asset."""

from pathlib import Path

import pytest

from meme_generator.infrastructure.images import LocalImageProvider


def test_local_image_is_copied(tmp_path: Path) -> None:
    """One numbered image is copied into the rendering workdir."""
    originals = tmp_path / 'originals'
    originals.mkdir()
    (originals / '1.png').write_bytes(b'fixture')
    output = tmp_path / 'downloaded'
    image = LocalImageProvider(originals).fetch('any query', 1, output)
    assert image.image_path.read_bytes() == b'fixture'
    assert image.license_name == 'User-provided'


def test_missing_image_fails(tmp_path: Path) -> None:
    """Missing scene images cause explicit rather than random fallback."""
    provider = LocalImageProvider(tmp_path)
    with pytest.raises(FileNotFoundError):
        provider.fetch('some text', 3, tmp_path / 'out')
