"""Run SQL migrations using Pydantic Settings and an explicit connection."""

from contextlib import ExitStack

from alembic import context
from sqlalchemy import Connection

from meme_generator.config.settings import GenerationSettings
from meme_generator.persistence.sqlalchemy.engine import (
    create_catalog_engine,
)
from meme_generator.persistence.sqlalchemy.models import CatalogBase


def run_migrations(connection: Connection) -> None:
    """Perform schema changes within Alembic's migration transaction."""
    context.configure(
        connection=connection,
        target_metadata=CatalogBase.metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def migrate_database(database_url: str) -> None:
    """Manage the configured engine lifetime even when migration fails."""
    with ExitStack() as resources:
        engine = create_catalog_engine(database_url)
        resources.callback(engine.dispose)
        with engine.connect() as connection:
            run_migrations(connection)


def run_online_migrations() -> None:
    """Use an injected test connection or an env-configured database."""
    supplied_connection: object = context.config.attributes.get('connection')
    if isinstance(supplied_connection, Connection):
        run_migrations(supplied_connection)
        return
    settings: GenerationSettings = GenerationSettings()
    database_url = settings.database.url
    if database_url is None:
        raise ValueError('Set MEMEGEN_DATABASE__URL before running migrations')
    migrate_database(database_url.get_secret_value())


if context.is_offline_mode():
    raise RuntimeError('Use online migrations with a real SQL connection')
run_online_migrations()
