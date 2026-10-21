"""Result of a completed generation request."""

from pathlib import Path

from pydantic import BaseModel, Field


class GeneratedVideo(BaseModel):
    """Location and public metadata of an exported MP4."""

    output_path: Path
    scene_count: int = Field(ge=1)
    theme: str = Field(min_length=1)
