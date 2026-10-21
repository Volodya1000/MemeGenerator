"""Explicit application command for importing validated local clips."""

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)


def import_memes(
    repository: SqlAlchemyMemeRepository,
    memes: list[Meme],
) -> int:
    """Provision a database with an approved complete clip collection."""
    repository.create_schema()
    repository.replace_all(memes)
    return len(memes)
