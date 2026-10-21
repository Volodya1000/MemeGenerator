"""A legally supplied reaction clip identified by a stable key."""

from pathlib import Path

from pydantic import BaseModel, Field


class Meme(BaseModel):
    """Exact phrase and filesystem location of one authorized clip."""

    meme_id: str = Field(min_length=1)
    phrase: str = Field(min_length=1)
    video_path: Path
