"""Real SQL connection fixtures for repository integration tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine

from meme_generator.infrastructure.database.engine import (
    create_catalog_engine,
)
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


@pytest.fixture
def database_engine(tmp_path: Path) -> Iterator[Engine]:
    """Use a fresh file database with realistic persistence per test."""
    engine = create_catalog_engine(
        f'sqlite+pysqlite:///{tmp_path / "catalog.sqlite3"}'
    )
    yield engine
    engine.dispose()


@pytest.fixture
def sql_repository(database_engine: Engine) -> SqlAlchemyMemeRepository:
    """Create an isolated catalog schema before integration assertions."""
    repository = SqlAlchemyMemeRepository(database_engine)
    repository.create_schema()
    return repository
