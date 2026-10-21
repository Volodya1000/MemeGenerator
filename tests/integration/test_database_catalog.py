"""Integration tests verify observable catalog state across SQL sessions."""

from pathlib import Path

import pytest
from sqlalchemy import Engine

from meme_generator.domain.meme import Meme
from meme_generator.persistence.sqlalchemy.repository import (
    SqlAlchemyMemeRepository,
)


def test_reactions_persist_across_instances(
    sql_repository: SqlAlchemyMemeRepository,
    database_engine: Engine,
    tmp_path: Path,
) -> None:
    """A new repository reads exactly what a previous instance committed."""
    first = Meme(
        meme_id='alpha',
        phrase='First phrase',
        video_path=tmp_path / 'alpha.mp4',
    )
    second = Meme(
        meme_id='beta',
        phrase='Second phrase',
        video_path=tmp_path / 'beta.mp4',
    )
    sql_repository.replace_all([second, first])
    reopened = SqlAlchemyMemeRepository(database_engine)
    assert reopened.all() == [second, first]
    assert reopened.get('beta') == second


def test_missing_id_is_reported(
    sql_repository: SqlAlchemyMemeRepository,
) -> None:
    """The adapter preserves the domain repository's missing-ID contract."""
    with pytest.raises(KeyError, match='not-present'):
        sql_repository.get('not-present')


def test_validation_preserves_existing_catalog(
    sql_repository: SqlAlchemyMemeRepository,
    tmp_path: Path,
) -> None:
    """A rejected duplicate batch must not destroy committed entries."""
    approved = Meme(
        meme_id='approved',
        phrase='Approved',
        video_path=tmp_path / 'approved.mp4',
    )
    sql_repository.replace_all([approved])
    with pytest.raises(ValueError, match='Duplicate'):
        sql_repository.replace_all([approved, approved])
    assert sql_repository.all() == [approved]


def test_empty_import_does_not_clear_catalog(
    sql_repository: SqlAlchemyMemeRepository,
    tmp_path: Path,
) -> None:
    """An accidental empty update cannot erase the reaction collection."""
    approved = Meme(
        meme_id='approved',
        phrase='Approved',
        video_path=tmp_path / 'approved.mp4',
    )
    sql_repository.replace_all([approved])
    with pytest.raises(ValueError, match='empty'):
        sql_repository.replace_all([])
    assert sql_repository.all() == [approved]


def test_repository_reopen_retains_commits(
    sql_repository: SqlAlchemyMemeRepository,
    database_engine: Engine,
    tmp_path: Path,
) -> None:
    """A failed SQL write preserves the last committed catalogue snapshot."""
    approved = Meme(
        meme_id='stable',
        phrase='Stable',
        video_path=tmp_path / 'stable.mp4',
    )
    sql_repository.replace_all([approved])
    assert SqlAlchemyMemeRepository(database_engine).all() == [approved]
