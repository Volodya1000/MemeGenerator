"""Catalog query contract, independent of JSON or database technology."""

from typing import Protocol

from meme_generator.domain.meme import Meme


class MemeRepositoryProtocol(Protocol):
    """Provide approved reaction clips by stable identifier."""

    def get(self, meme_id: str) -> Meme:
        """Return one existing reaction or raise KeyError."""
        ...

    def all(self) -> list[Meme]:
        """Return a snapshot of all approved reactions."""
        ...
