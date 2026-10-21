"""Validated ordered plan for an entire themed video."""

from typing import Self

from pydantic import BaseModel, Field, model_validator

from meme_generator.domain.scene import Scene


class Scenario(BaseModel):
    """Require nonempty scenes in contiguous playback order."""

    theme: str = Field(min_length=1)
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_scene_order(self) -> Self:
        """Reject duplicate, missing, or out-of-order scene numbers."""
        expected = list(range(1, len(self.scenes) + 1))
        actual = [scene.order for scene in self.scenes]
        if actual != expected:
            raise ValueError('Scene orders must start at 1 and be contiguous')
        return self
