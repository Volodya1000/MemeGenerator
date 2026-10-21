"""Business-facing catalog import operation; no ORM dependencies."""

from meme_generator.application.protocols.catalog_writer import (
    CatalogWriterProtocol,
)
from meme_generator.domain.meme import Meme


def import_memes(repository: CatalogWriterProtocol, memes: list[Meme]) -> int:
    """Write a complete approved catalog through a storage-independent port."""
    repository.replace_all(memes)
    return len(memes)
