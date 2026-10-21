"""SQLite rollback protects committed catalog data on database failure."""

from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.database.engine import (
    create_catalog_engine,
)
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


def test_failed_import_preserves_committed_rows(tmp_path: Path) -> None:
    """A constraint violation after DELETE rolls back the whole import."""
    engine: Engine = create_catalog_engine(
        f'sqlite+pysqlite:///{tmp_path}/catalog.sqlite3'
    )
    repository = SqlAlchemyMemeRepository(engine)
    repository.create_schema()
    approved = Meme(
        meme_id='original',
        phrase='Previously approved',
        video_path=tmp_path / 'original.mp4',
    )
    repository.replace_all([approved])
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER prevent_insert BEFORE INSERT ON meme_clips "
                "BEGIN SELECT RAISE(ABORT, 'import blocked'); END"
            ),
        )
    replacement = Meme(
        meme_id='new',
        phrase='Replacement',
        video_path=tmp_path / 'new.mp4',
    )
    with pytest.raises(DBAPIError, match='import blocked'):
        repository.replace_all([replacement])
    assert repository.all() == [approved]
    engine.dispose()
