"""Properties of a decoded video clip."""

from pydantic import BaseModel, Field


class ClipInfo(BaseModel):
    """Validated FFprobe stream metadata."""

    duration_seconds: float = Field(gt=0)
    has_audio: bool
