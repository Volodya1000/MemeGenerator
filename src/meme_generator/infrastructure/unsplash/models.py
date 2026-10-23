"""Strictly parsed Unsplash photo search response contracts."""

from pydantic import BaseModel, Field, HttpUrl


class UnsplashUrls(BaseModel):
    """Hotlinked image URL returned by Unsplash."""

    regular: HttpUrl


class UnsplashLinks(BaseModel):
    """Image page and download-tracking endpoint."""

    html: HttpUrl
    download_location: HttpUrl


class UnsplashUserLinks(BaseModel):
    """Original photographer profile URL."""

    html: HttpUrl


class UnsplashUser(BaseModel):
    """Photographer attribution fields."""

    name: str = Field(min_length=1)
    links: UnsplashUserLinks


class UnsplashPhoto(BaseModel):
    """Search candidate with source dimensions and download metadata."""

    id: str = Field(min_length=1)
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    urls: UnsplashUrls
    links: UnsplashLinks
    user: UnsplashUser


class UnsplashResponse(BaseModel):
    """Public photo search results."""

    photos: list[UnsplashPhoto] = Field(default_factory=list, alias='results')
