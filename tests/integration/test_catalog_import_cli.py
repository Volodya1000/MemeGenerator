"""Import command persists a validated catalog through the CLI."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from meme_generator.cli import app
from meme_generator.infrastructure.database.engine import (
    create_catalog_engine,
)
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)

REACTION_ID = 'reaction-id'


def test_import_command_persists_clips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An actual CLI call commits rows that another session can read."""
    (tmp_path / 'reaction.mp4').touch()
    manifest = tmp_path / 'memes.json'
    manifest.write_text(
        json.dumps([
            {
                'meme_id': REACTION_ID,
                'phrase': 'A reaction',
                'video_path': 'reaction.mp4',
            },
        ]),
        encoding='utf-8',
    )
    database_path = tmp_path / 'memes.sqlite3'
    url = f'sqlite+pysqlite:///{database_path}'
    monkeypatch.setenv('MEMEGEN_DATABASE_URL', url)
    outcome = CliRunner().invoke(
        app,
        ['catalog', 'import', '--source', str(manifest)],
    )
    assert outcome.exit_code == 0
    assert 'Imported 1 reactions' in outcome.output
    repository = SqlAlchemyMemeRepository(create_catalog_engine(url))
    assert repository.get(REACTION_ID).phrase == 'A reaction'
