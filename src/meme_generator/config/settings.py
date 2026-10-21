"""Configuration schema validated at the application boundary."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerationSettings(BaseModel):
    """Non-secret video generation and external adapter settings."""

    model_config = ConfigDict(extra='forbid', strict=True)

    planner: Literal['llm', 'demo'] = 'llm'
    model: str = ''
    api_base: str | None = None
    scenes: int = Field(default=5, ge=1)
    catalog: Path = Path('assets/memes.json')
    output: Path = Path('output/result.mp4')
    images: Literal['commons', 'local'] = 'commons'
    image_dir: Path | None = None
