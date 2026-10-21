"""Typed configuration independent of command-line parsing."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerationSettings(BaseModel):
    """Validated, non-secret settings for one video-generation request."""

    model_config = ConfigDict(extra='forbid', strict=True)

    planner: Literal['llm', 'demo'] = 'llm'
    model: str = ''
    api_base: str | None = None
    scenes: int = Field(default=5, ge=1)
    catalog: Path = Path('assets/memes.json')
    catalog_backend: Literal['json', 'sqlalchemy'] = 'json'
    output: Path = Path('output/result.mp4')
    images: Literal['commons', 'local'] = 'commons'
    image_dir: Path | None = None
