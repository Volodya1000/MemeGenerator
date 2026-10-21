"""Compose storage ports from either a local JSON or SQL database."""

from pathlib import Path

from meme_generator.application.catalog_import import import_memes
from meme_generator.application.protocols.meme_repository import MemeRepositoryProtocol
from meme_generator.config.loader import database_url
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.in_memory_meme_repository import InMemoryMemeRepository
from meme_generator.persistence.sqlalchemy.engine import (
    create_catalog_engine,
)
from meme_generator.persistence.sqlalchemy.repository import (
    SqlAlchemyMemeRepository,
)


def create_database_catalog() -> SqlAlchemyMemeRepository:
    """Connect to any installed SQLAlchemy dialect using env credentials."""
    url = database_url()
    if not url:
        raise ValueError('Set MEMEGEN_DATABASE_URL for SQL catalog')
    return SqlAlchemyMemeRepository(create_catalog_engine(url))


def create_catalog(settings: GenerationSettings) -> MemeRepositoryProtocol:
    """Return the configured catalog without leaking storage details."""
    if settings.catalog_backend == 'sqlalchemy':
        return create_database_catalog()
    return InMemoryMemeRepository.from_json(settings.catalog)


def import_catalog_file(source: Path) -> int:
    """Provision SQL storage and atomically import one validated JSON file."""
    catalog = InMemoryMemeRepository.from_json(source)
    repository = create_database_catalog()
    repository.create_schema()
    return import_memes(repository, catalog.all())
