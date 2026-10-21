"""Validated descriptions of externally provided reaction clips."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class MemeSource(BaseModel):
    """Curated reference and optional direct media URL for one reaction."""

    model_config = ConfigDict(extra='forbid', frozen=True)

    meme_id: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    phrase: str = Field(min_length=1)
    source_page: HttpUrl
    media_url: HttpUrl | None = None
    sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')


class MemeSources(BaseModel):
    """Versioned source manifest with stable unique identifiers."""

    model_config = ConfigDict(extra='forbid', frozen=True)

    schema_version: Literal[1]
    clips: list[MemeSource] = Field(min_length=1)

    @model_validator(mode='after')
    def ensure_unique_identifiers(self) -> Self:
        """Reject ambiguous filenames and catalog identifiers."""
        identifiers = [clip.meme_id for clip in self.clips]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError('Meme identifiers must be unique')
        return self
