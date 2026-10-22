"""Validated Pexels queries and size-aware ranked image selection."""

from typing import Literal

from pydantic import BaseModel, Field

from meme_generator.config.pexels import (
    MAX_SEARCH_LIMIT,
    PexelsSettings,
)
from meme_generator.infrastructure.pexels.models import PexelsPhoto

PEXELS_SEARCH_URL = 'https://api.pexels.com/v1/search'
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 360


class PexelsSearchRequest(BaseModel):
    """Public, non-secret parameters for Pexels image search."""

    query: str = Field(min_length=1)
    orientation: Literal['landscape', 'portrait', 'square']
    size: Literal['large', 'medium', 'small']
    per_page: int = Field(ge=1, le=MAX_SEARCH_LIMIT)


def search_parameters(
    query: str,
    settings: PexelsSettings,
) -> dict[str, str | int]:
    """Build a validated query without leaking the authentication key."""
    request = PexelsSearchRequest(
        query=query,
        orientation=settings.orientation,
        size=settings.size,
        per_page=settings.per_page,
    )
    return request.model_dump()


def choose_photo(photos: list[PexelsPhoto]) -> PexelsPhoto:
    """Use Pexels ranking while enforcing a usable photo resolution."""
    for photo in photos:
        if (
            photo.width >= MIN_IMAGE_WIDTH
            and photo.height >= MIN_IMAGE_HEIGHT
        ):
            return photo
    raise ValueError('No usable Pexels photograph found')
