"""Verify Alembic's actual upgrade/downgrade against real SQL engines."""

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, inspect

MIGRATION_CONFIG = 'alembic.ini'
MEME_TABLE = 'meme_clips'


def migrate(connection: Connection, revision: str) -> None:
    """Apply a migration on an explicitly supplied test connection."""
    config = Config(MIGRATION_CONFIG)
    config.attributes['connection'] = connection
    if revision == 'head':
        command.upgrade(config, revision)
    else:
        command.downgrade(config, revision)


def test_initial_revision_round_trip(database_engine: Engine) -> None:
    """Upgrade creates the exact SQL schema and downgrade removes it."""
    with database_engine.connect() as connection:
        migrate(connection, 'head')
    inspector = inspect(database_engine)
    assert MEME_TABLE in inspector.get_table_names()
    columns = {column['name'] for column in inspector.get_columns(MEME_TABLE)}
    assert columns == {'meme_id', 'phrase', 'video_path', 'position'}
    with database_engine.connect() as connection:
        migrate(connection, 'base')
    assert MEME_TABLE not in inspect(database_engine).get_table_names()
