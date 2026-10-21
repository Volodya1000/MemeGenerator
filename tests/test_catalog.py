"""Catalog reads and validates user-provided clips."""

import json
from pathlib import Path

import pytest

from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)

CLIP_NAME = 'clip.mp4'
REACTION_ID = 'reaction-1'


def test_read_catalog(tmp_path: Path) -> None:
    """Relative clip paths are normalized and identifiers remain stable."""
    clip = tmp_path / CLIP_NAME
    clip.touch()
    catalog_path = tmp_path / 'memes.json'
    entries = [
        {
            'meme_id': REACTION_ID,
            'phrase': 'Very surprised',
            'video_path': CLIP_NAME,
        },
    ]
    catalog_path.write_text(json.dumps(entries), encoding='utf-8')

    catalog = InMemoryMemeRepository.from_json(catalog_path)

    assert catalog.get(REACTION_ID).video_path == clip.resolve()
    assert len(catalog) == 1


def test_duplicate_meme_id_fails(tmp_path: Path) -> None:
    """Duplicate identifiers are never silently replaced."""
    clip = tmp_path / CLIP_NAME
    clip.touch()
    catalog_path = tmp_path / 'memes.json'
    entry = {
        'meme_id': REACTION_ID,
        'phrase': 'Wow',
        'video_path': CLIP_NAME,
    }
    catalog_path.write_text(json.dumps([entry, entry]), encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'):
        InMemoryMemeRepository.from_json(catalog_path)


def test_parent_path_escape_fails(tmp_path: Path) -> None:
    """The catalog cannot reference files outside its own directory."""
    catalog_path = tmp_path / 'memes.json'
    entries = [
        {
            'meme_id': REACTION_ID,
            'phrase': 'Wow',
            'video_path': '../escaped.mp4',
        },
    ]
    catalog_path.write_text(json.dumps(entries), encoding='utf-8')
    with pytest.raises(ValueError, match='inside'):
        InMemoryMemeRepository.from_json(catalog_path)
