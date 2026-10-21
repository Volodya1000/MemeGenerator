"""Business-facing catalog import operation; no ORM dependencies."""

from meme_generator.application.ports.catalog_writer import CatalogWriter
from meme_generator.domain.meme import Meme


def import_memes(repository: CatalogWriter, memes: list[Meme]) -> int:
    """Write a complete approved catalog through a storage-independent port."""
    repository.replace_all(memes)
    return len(memes)
