"""Validated JSON catalog of legally provided reaction clips."""

import json
from pathlib import Path

from pydantic import TypeAdapter

from meme_generator.domain.models import Meme

VIDEO_SUFFIXES = frozenset(('.mp4', '.mov', '.webm'))


def resolve_video(meme: Meme, directory: Path) -> Meme:
    """Reject unsafe paths, missing clips and unsupported extensions."""
    resolved = (directory / meme.video_path).resolve()
    if not resolved.is_relative_to(directory):
        raise ValueError('Meme video must be inside the catalog folder')
    if resolved.suffix.lower() not in VIDEO_SUFFIXES:
        raise ValueError('Meme video has an unsupported extension')
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return meme.model_copy(update={'video_path': resolved})


class MemeCatalog:
    """Load a curated catalog without searching for celebrity videos."""

    def __init__(self, memes: list[Meme]) -> None:
        """Store nonempty reactions indexed by stable identifiers."""
        if not memes:
            raise ValueError('Catalog must contain at least one meme')
        self._memes = {meme.meme_id: meme for meme in memes}
        if len(self._memes) != len(memes):
            raise ValueError('Duplicate meme identifiers')

    def __len__(self) -> int:
        """Return how many reactions are usable."""
        return len(self._memes)

    @classmethod
    def from_json(cls, path: Path) -> 'MemeCatalog':
        """Load JSON and resolve paths relative to the catalog folder."""
        directory = path.resolve().parent
        raw_data = json.loads(path.read_text(encoding='utf-8'))
        parsed = TypeAdapter(list[Meme]).validate_python(raw_data)
        memes = [resolve_video(meme, directory) for meme in parsed]
        return cls(memes)

    def get(self, meme_id: str) -> Meme:
        """Return a known clip or fail for unknown identifiers."""
        return self._memes[meme_id]

    def all(self) -> list[Meme]:
        """Return a snapshot of all curated reactions."""
        return list(self._memes.values())
