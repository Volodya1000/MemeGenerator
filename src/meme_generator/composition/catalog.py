"""Select a database or JSON repository without affecting use cases."""

from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.config.loader import database_url
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.database.engine import (
    create_catalog_engine,
)
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


def create_database_catalog() -> SqlAlchemyMemeRepository:
    """Connect using an explicit SQLAlchemy dialect URL."""
    url = database_url()
    if not url:
        raise ValueError('Set MEMEGEN_DATABASE_URL for SQL catalog')
    return SqlAlchemyMemeRepository(create_catalog_engine(url))


def create_catalog(settings: GenerationSettings) -> MemeRepository:
    """Return a repository according to the selected storage backend."""
    if settings.catalog_backend == 'sqlalchemy':
        return create_database_catalog()
    return MemeCatalog.from_json(settings.catalog)
