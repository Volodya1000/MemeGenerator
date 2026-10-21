"""Validated inputs and outputs of the video-generation pipeline."""

from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator


class Meme(BaseModel):
    """A reaction video and its exact phrase."""

    meme_id: str = Field(min_length=1)
    phrase: str = Field(min_length=1)
    video_path: Path


class Scene(BaseModel):
    """One contextual image followed by a reaction video."""

    order: int = Field(ge=1)
    description: str = Field(min_length=1)
    image_query: str = Field(min_length=1)
    meme_id: str = Field(min_length=1)


class Scenario(BaseModel):
    """Ordered, nonempty scenes for a user's topic."""

    theme: str = Field(min_length=1)
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_scene_order(self) -> Self:
        """Require a contiguous order without repeated scene numbers."""
        expected = list(range(1, len(self.scenes) + 1))
        actual = [scene.order for scene in self.scenes]
        if actual != expected:
            raise ValueError('Scene orders must start at 1 and be contiguous')
        return self


class GeneratedVideo(BaseModel):
    """Location and metadata of an exported video."""

    output_path: Path
    scene_count: int = Field(ge=1)
    theme: str = Field(min_length=1)
