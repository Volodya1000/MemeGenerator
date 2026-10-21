"""Validation and provenance contracts for curated clips."""

import pytest
from pydantic import ValidationError

from meme_generator.domain.meme_sources import MemeSources


def source_record(identifier: str = 'reaction') -> dict[str, str]:
    """Build a minimal source definition for tests."""
    return {
        'meme_id': identifier,
        'phrase': 'Reaction',
        'source_page': 'https://cutzo.ru/video/example',
    }


def source_manifest(*clips: dict[str, str]) -> dict[str, object]:
    """Create the versioned manifest without repeated magic keys."""
    return {'schema_version': 1, 'clips': clips}


def test_manifest_accepts_curated_source() -> None:
    """An HTTPS page is sufficient for offline asset import."""
    manifest = MemeSources.model_validate(source_manifest(source_record()))
    assert manifest.clips[0].meme_id == 'reaction'
    assert manifest.clips[0].media_url is None


@pytest.mark.parametrize('identifier', ['../unsafe', 'bad-name', '/unsafe'])
def test_rejects_unsafe_identifier(identifier: str) -> None:
    """User-provided identifiers must never escape the asset directory."""
    with pytest.raises(ValidationError):
        MemeSources.model_validate(
            source_manifest(source_record(identifier)),
        )


def test_rejects_repeated_identifier() -> None:
    """Duplicate clips would overwrite each other's generated files."""
    duplicate = source_record()
    with pytest.raises(ValidationError, match='unique'):
        MemeSources.model_validate(source_manifest(duplicate, duplicate))


def test_rejects_unknown_manifest_field() -> None:
    """Typos in source definitions must not be ignored silently."""
    source = source_record()
    source['video_url'] = 'https://cdn.example.com/video.mp4'
    with pytest.raises(ValidationError):
        MemeSources.model_validate(source_manifest(source))
