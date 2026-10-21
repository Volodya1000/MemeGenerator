"""Negative repository contracts independent of rendering or planning."""

import json
from pathlib import Path

import pytest

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.catalog import MemeCatalog

REACTION_ID = 'reaction-1'
CLIP_NAME = 'clip.mp4'


def test_missing_clip_is_rejected(tmp_path: Path) -> None:
    """Catalog creation refuses a reference to a missing media file."""
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
    """A text file cannot be used as an allegedly supported video clip."""
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
    """Repository lookup reports an unknown key consistently."""
    catalog = MemeCatalog([
        Meme(meme_id='known', phrase='Known', video_path=Path('clip.mp4')),
    ])
    with pytest.raises(KeyError):
        catalog.get('missing')
