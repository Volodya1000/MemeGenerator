"""Adapter selection by configuration, tested without model calls."""

from pathlib import Path

import pytest

from meme_generator.bootstrap import create_catalog
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


def test_json_backend_selects_local_catalog(tmp_path: Path) -> None:
    """Default configuration selects a local JSON repository."""
    clip = tmp_path / 'clip.mp4'
    clip.touch()
    manifest = tmp_path / 'memes.json'
    manifest.write_text(
        '[{"meme_id":"a","phrase":"test","video_path":"clip.mp4"}]',
        encoding='utf-8',
    )
    repository = create_catalog(GenerationSettings(catalog=manifest))
    assert isinstance(repository, MemeCatalog)
    assert repository.get('a').video_path == clip.resolve()


def test_sql_backend_uses_environment_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Database provider can be swapped without changing the use case."""
    db_path = tmp_path / 'memes.sqlite3'
    monkeypatch.setenv(
        'MEMEGEN_DATABASE_URL', f'sqlite+pysqlite:///{db_path}',
    )
    repository = create_catalog(
        GenerationSettings(catalog_backend='sqlalchemy')
    )
    assert isinstance(repository, SqlAlchemyMemeRepository)


def test_sql_backend_without_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing database credentials are not replaced by a hidden default."""
    monkeypatch.delenv('MEMEGEN_DATABASE_URL', raising=False)
    with pytest.raises(ValueError, match='MEMEGEN_DATABASE_URL'):
        create_catalog(GenerationSettings(catalog_backend='sqlalchemy'))
