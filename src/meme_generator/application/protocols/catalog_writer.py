"""Write-side catalog contract for explicit imports."""

from typing import Protocol

from meme_generator.domain.meme import Meme


class CatalogWriterProtocol(Protocol):
    """Atomically replace the complete reaction collection."""

    def replace_all(self, memes: list[Meme]) -> None:
        """Persist all reactions or leave the previous state unchanged."""
        ...
