"""Real SQLite or PostgreSQL connections, with isolated test schemas."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine

from meme_generator.persistence.sqlalchemy.engine import (
    create_catalog_engine,
)
from meme_generator.persistence.sqlalchemy.models import CatalogBase
from meme_generator.persistence.sqlalchemy.repository import (
    SqlAlchemyMemeRepository,
)


@pytest.fixture
def database_engine(tmp_path: Path) -> Iterator[Engine]:
    """Run real SQL tests on SQLite or a configured PostgreSQL service."""
    database_path = tmp_path / 'catalog.sqlite3'
    local_url = f'sqlite+pysqlite:///{database_path}'
    database_url = os.getenv('MEMEGEN_TEST_POSTGRES_URL', local_url)
    engine = create_catalog_engine(database_url)
    yield engine
    CatalogBase.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sql_repository(database_engine: Engine) -> SqlAlchemyMemeRepository:
    """Provision a clean catalog for behavioral integration tests."""
    repository = SqlAlchemyMemeRepository(database_engine)
    repository.create_schema()
    return repository
