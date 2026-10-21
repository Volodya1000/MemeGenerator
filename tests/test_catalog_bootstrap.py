"""Verify selection of a SQL or in-memory catalog adapter."""

from pathlib import Path

import pytest

from meme_generator.composition.catalog import create_catalog
from meme_generator.config.settings import (
    DatabaseSettings,
    GenerationSettings,
)
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from meme_generator.persistence.sqlalchemy.repository import (
    SqlAlchemyMemeRepository,
)


def test_json_backend_selects_local_catalog(tmp_path: Path) -> None:
    """The default adapter loads a validated local JSON catalog."""
    clip: Path = tmp_path / 'clip.mp4'
    clip.touch()
    manifest: Path = tmp_path / 'memes.json'
    manifest.write_text(
        '[{"meme_id":"a","phrase":"test","video_path":"clip.mp4"}]',
        encoding='utf-8',
    )
    repository = create_catalog(GenerationSettings(catalog=manifest))
    assert isinstance(repository, InMemoryMemeRepository)
    assert repository.get('a').video_path == clip.resolve()


def test_sql_backend_uses_typed_environment_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pydantic Settings resolves a SQL URL without reading os.getenv."""
    db_path: Path = tmp_path / 'memes.sqlite3'
    monkeypatch.setenv(
        'MEMEGEN_DATABASE__URL',
        f'sqlite+pysqlite:///{db_path}',
    )
    repository = create_catalog(
        GenerationSettings(database=DatabaseSettings(backend='sqlalchemy'))
    )
    assert isinstance(repository, SqlAlchemyMemeRepository)


def test_sql_backend_without_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No SQL backend starts with a missing database URL."""
    monkeypatch.delenv('MEMEGEN_DATABASE__URL', raising=False)
    with pytest.raises(ValueError, match='MEMEGEN_DATABASE__URL'):
        create_catalog(
            GenerationSettings(database=DatabaseSettings(backend='sqlalchemy'))
        )
