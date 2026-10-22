"""Validated shapes for Wikimedia Commons API responses."""

from pydantic import BaseModel, Field


class CommonsMetadataField(BaseModel):
    """Wikimedia metadata values may be strings or numeric measurements."""

    value: str | float


class CommonsImage(BaseModel):
    """Search-result dimensions, URLs, media type, and attribution."""

    url: str
    mime: str
    width: int
    height: int
    thumburl: str | None = None
    descriptionurl: str | None = None
    extmetadata: dict[str, CommonsMetadataField] = Field(default_factory=dict)


class CommonsPage(BaseModel):
    """One image file page returned by the search API."""

    title: str
    imageinfo: list[CommonsImage] = Field(default_factory=list)


class CommonsQuery(BaseModel):
    """Pages matched by the Wikimedia search query."""

    pages: dict[str, CommonsPage] = Field(default_factory=dict)


class CommonsResponse(BaseModel):
    """Typed boundary for the third-party search API."""

    query: CommonsQuery = Field(default_factory=CommonsQuery)
