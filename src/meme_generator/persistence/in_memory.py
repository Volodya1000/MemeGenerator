"""Validated JSON catalog of legally supplied reaction clips."""

import json
from pathlib import Path

from pydantic import TypeAdapter

from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.domain.meme import Meme

VIDEO_SUFFIXES = frozenset(('.mp4', '.mov', '.webm'))


def resolve_video(meme: Meme, directory: Path) -> Meme:
    """Reject unsafe paths, missing clips, and unsupported extensions."""
    resolved = (directory / meme.video_path).resolve()
    if not resolved.is_relative_to(directory):
        raise ValueError('Meme video must be inside the catalog folder')
    if resolved.suffix.lower() not in VIDEO_SUFFIXES:
        raise ValueError('Meme video has an unsupported extension')
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return meme.model_copy(update={'video_path': resolved})


class InMemoryMemeRepository(MemeRepositoryProtocol):
    """In-memory repository, optionally loaded from a JSON manifest."""

    def __init__(self, memes: list[Meme]) -> None:
        """Reject ambiguous or empty reaction repositories."""
        if not memes:
            raise ValueError('Catalog must contain at least one meme')
        self._memes = {meme.meme_id: meme for meme in memes}
        if len(self._memes) != len(memes):
            raise ValueError('Duplicate meme identifiers')

    def __len__(self) -> int:
        """Return the number of approved reactions."""
        return len(self._memes)

    @classmethod
    def from_json(cls, path: Path) -> 'InMemoryMemeRepository':
        """Load a file-backed repository with safe relative media paths."""
        directory = path.resolve().parent
        raw_data = json.loads(path.read_text(encoding='utf-8'))
        parsed = TypeAdapter(list[Meme]).validate_python(raw_data)
        memes = [resolve_video(meme, directory) for meme in parsed]
        return cls(memes)

    def get(self, meme_id: str) -> Meme:
        """Return an approved clip by identifier."""
        return self._memes[meme_id]

    def all(self) -> list[Meme]:
        """Return a snapshot without exposing internal mutable mappings."""
        return list(self._memes.values())
