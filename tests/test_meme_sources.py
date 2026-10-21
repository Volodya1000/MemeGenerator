"""Validation and provenance contracts for curated clips."""

import pytest
from pydantic import ValidationError

from meme_generator.domain.meme_sources import MemeSources


def test_manifest_accepts_curated_source() -> None:
    """An HTTPS page is sufficient for offline asset import."""
    manifest = MemeSources.model_validate(
        {
            'schema_version': 1,
            'clips': [
                {
                    'meme_id': 'tinkov_kruto',
                    'phrase': 'Круто!',
                    'source_page': 'https://cutzo.ru/video/example',
                },
            ],
        },
    )
    assert manifest.clips[0].meme_id == 'tinkov_kruto'
    assert manifest.clips[0].media_url is None


@pytest.mark.parametrize('identifier', ('../unsafe', 'bad-name', '/tmp/x'))
def test_rejects_unsafe_identifier(identifier: str) -> None:
    """User-provided identifiers must never escape the asset directory."""
    with pytest.raises(ValidationError):
        MemeSources.model_validate(
            {
                'schema_version': 1,
                'clips': [
                    {
                        'meme_id': identifier,
                        'phrase': 'Phrase',
                        'source_page': 'https://cutzo.ru/video/example',
                    },
                ],
            },
        )


def test_rejects_repeated_identifier() -> None:
    """Duplicate clips would overwrite each other's generated files."""
    entry = {
        'meme_id': 'reaction',
        'phrase': 'Reaction',
        'source_page': 'https://cutzo.ru/video/example',
    }
    with pytest.raises(ValidationError, match='unique'):
        MemeSources.model_validate(
            {'schema_version': 1, 'clips': [entry, entry]},
        )


def test_rejects_unknown_manifest_field() -> None:
    """Typos in source definitions must not be ignored silently."""
    with pytest.raises(ValidationError):
        MemeSources.model_validate(
            {
                'schema_version': 1,
                'clips': [
                    {
                        'meme_id': 'example',
                        'phrase': 'Phrase',
                        'source_page': 'https://cutzo.ru/video/example',
                        'video_url': 'https://cdn.example.com/video.mp4',
                    },
                ],
            },
        )
