"""Catalog reads and validates user-provided clips."""

import json
from pathlib import Path

import pytest

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.catalog import MemeCatalog

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

    catalog = MemeCatalog.from_json(catalog_path)

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
        MemeCatalog.from_json(catalog_path)


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
        MemeCatalog.from_json(catalog_path)


def test_missing_clip_is_rejected(tmp_path: Path) -> None:
    """The catalog never accepts a reference to an absent movie file."""
    path = tmp_path / 'memes.json'
    path.write_text(
        json.dumps([
            {'meme_id': REACTION_ID, 'phrase': 'surprise', 'video_path': CLIP_NAME},
        ]),
        encoding='utf-8',
    )
    with pytest.raises(FileNotFoundError):
        MemeCatalog.from_json(path)


def test_unsupported_video_extension_is_rejected(tmp_path: Path) -> None:
    """A renamed image cannot be passed to the video renderer as a clip."""
    path = tmp_path / 'memes.json'
    (tmp_path / 'bad.txt').write_text('not a video', encoding='utf-8')
    path.write_text(
        json.dumps([
            {'meme_id': REACTION_ID, 'phrase': 'surprise', 'video_path': 'bad.txt'},
        ]),
        encoding='utf-8',
    )
    with pytest.raises(ValueError, match='unsupported extension'):
        MemeCatalog.from_json(path)


def test_unknown_reaction_id_raises_key_error() -> None:
    """Repository retrieval has explicit absent-identifier semantics."""
    catalog = MemeCatalog([
        Meme(meme_id='known', phrase='Known', video_path=Path('clip.mp4')),
    ])
    with pytest.raises(KeyError):
        catalog.get('missing')
