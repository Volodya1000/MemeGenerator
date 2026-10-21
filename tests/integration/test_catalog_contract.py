"""Both adapters satisfy the same observable repository contract."""

from pathlib import Path

import pytest
from sqlalchemy import Engine

from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


@pytest.fixture(params=('memory', 'sql'))
def catalog_repository(
    request: pytest.FixtureRequest,
    database_engine: Engine,
    tmp_path: Path,
) -> MemeRepository:
    """Run identical state assertions against both concrete adapters."""
    reaction = Meme(
        meme_id='reaction',
        phrase='Reaction phrase',
        video_path=tmp_path / 'reaction.mp4',
    )
    if request.param == 'memory':
        return MemeCatalog([reaction])
    repository = SqlAlchemyMemeRepository(database_engine)
    repository.create_schema()
    repository.replace_all([reaction])
    return repository


def test_lookup_returns_exact_domain_data(
    catalog_repository: MemeRepository,
    tmp_path: Path,
) -> None:
    """Adapter internals cannot affect the publicly observable clip."""
    expected = Meme(
        meme_id='reaction',
        phrase='Reaction phrase',
        video_path=tmp_path / 'reaction.mp4',
    )
    assert catalog_repository.get('reaction') == expected


def test_unknown_key_has_same_error(catalog_repository: MemeRepository) -> None:
    """All implementations agree on missing-identifier semantics."""
    with pytest.raises(KeyError):
        catalog_repository.get('missing')


def test_snapshot_mutation_does_not_change_repository(
    catalog_repository: MemeRepository,
) -> None:
    """A caller mutating its returned list cannot alter stored clips."""
    snapshot = catalog_repository.all()
    snapshot.clear()
    assert len(catalog_repository.all()) == 1
