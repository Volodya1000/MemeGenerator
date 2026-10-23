"""Validate search parameters and select a sufficiently large photo."""

from typing import Literal

from pydantic import BaseModel, Field

from meme_generator.config.unsplash import MAX_SEARCH_LIMIT, UnsplashSettings
from meme_generator.infrastructure.unsplash.models import UnsplashPhoto

UNSPLASH_SEARCH_URL = 'https://api.unsplash.com/search/photos'
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 360


class UnsplashSearchRequest(BaseModel):
    """Public request parameters, never including the API credential."""

    query: str = Field(min_length=1)
    orientation: Literal['landscape', 'portrait', 'squarish']
    per_page: int = Field(ge=1, le=MAX_SEARCH_LIMIT)


def search_parameters(
    query: str,
    settings: UnsplashSettings,
) -> dict[str, str | int]:
    """Validate and serialize search input."""
    request = UnsplashSearchRequest(
        query=query,
        orientation=settings.orientation,
        per_page=settings.per_page,
    )
    return request.model_dump()


def choose_photo(photos: list[UnsplashPhoto]) -> UnsplashPhoto:
    """Prefer the provider's ranking without using tiny images."""
    for photo in photos:
        if photo.width >= MIN_IMAGE_WIDTH and photo.height >= MIN_IMAGE_HEIGHT:
            return photo
    raise ValueError('No usable Unsplash photograph found')
