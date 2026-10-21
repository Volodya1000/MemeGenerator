"""Wire in-memory or SQL persistence through typed application protocols."""

from pathlib import Path

from meme_generator.application.catalog_import import import_memes
from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.config.settings import GenerationSettings
from meme_generator.persistence.in_memory import (
    InMemoryMemeRepository,
)
from meme_generator.persistence.sqlalchemy.engine import create_catalog_engine
from meme_generator.persistence.sqlalchemy.repository import (
    SqlAlchemyMemeRepository,
)


def create_database_catalog(
    settings: GenerationSettings,
) -> SqlAlchemyMemeRepository:
    """Require an explicit database URL stored as a secret."""
    url = settings.database.url
    if url is None:
        raise ValueError('Set MEMEGEN_DATABASE__URL for SQL catalog')
    return SqlAlchemyMemeRepository(
        create_catalog_engine(url.get_secret_value())
    )


def create_catalog(settings: GenerationSettings) -> MemeRepositoryProtocol:
    """Choose storage without changing the downstream use case."""
    if settings.database.backend == 'sqlalchemy':
        return create_database_catalog(settings)
    return InMemoryMemeRepository.from_json(settings.catalog)


def import_catalog_file(
    source: Path,
    settings: GenerationSettings,
) -> int:
    """Validate local clips and atomically import them into SQL."""
    catalog = InMemoryMemeRepository.from_json(source)
    repository = create_database_catalog(settings)
    return import_memes(repository, catalog.all())
