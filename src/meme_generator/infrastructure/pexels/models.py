"""Typed records returned by the Pexels photo search endpoint."""

from pydantic import BaseModel, Field, HttpUrl


class PexelsSources(BaseModel):
    """URLs for downloadable photo renditions."""

    landscape: HttpUrl


class PexelsPhoto(BaseModel):
    """One photo and its required author attribution metadata."""

    width: int = Field(ge=1)
    height: int = Field(ge=1)
    url: HttpUrl
    photographer: str = Field(min_length=1)
    photographer_url: HttpUrl
    src: PexelsSources


class PexelsResponse(BaseModel):
    """Search response containing ranked candidate photographs."""

    photos: list[PexelsPhoto] = Field(default_factory=list)
