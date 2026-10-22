"""Typed Commons API query and image-selection rules."""

from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter

from meme_generator.infrastructure.commons.models import CommonsPage

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 360
SEARCH_LIMIT = 15
SEARCH_IMAGE_WIDTH = 1280
SUPPORTED_MIME = frozenset(('image/jpeg', 'image/png', 'image/webp'))


class CommonsSearchRequest(BaseModel):
    """Validate the exact Wikimedia parameters, including search query."""

    action: Literal['query'] = 'query'
    format: Literal['json'] = 'json'
    generator: Literal['search'] = 'search'
    gsrsearch: str = Field(min_length=1)
    gsrnamespace: int = 6
    gsrlimit: int = SEARCH_LIMIT
    prop: Literal['imageinfo'] = 'imageinfo'
    iiprop: Literal['url|size|mime|extmetadata'] = 'url|size|mime|extmetadata'
    iiurlwidth: int = SEARCH_IMAGE_WIDTH


def search_parameters(query: str) -> dict[str, str | int]:
    """Return a validated URL query without unchecked ad-hoc strings."""
    request = CommonsSearchRequest(gsrsearch=query)
    return TypeAdapter(dict[str, str | int]).validate_python(
        request.model_dump()
    )


def is_usable(page: CommonsPage) -> bool:
    """Accept only reasonably sized JPEG, PNG, or WebP images."""
    if not page.imageinfo:
        return False
    metadata = page.imageinfo[0]
    return (
        metadata.mime in SUPPORTED_MIME
        and metadata.width >= MIN_IMAGE_WIDTH
        and metadata.height >= MIN_IMAGE_HEIGHT
    )


def _title_words(page: CommonsPage) -> set[str]:
    """Normalize the visible Commons filename for lexical relevance."""
    return set(page.title.lower().replace('_', ' ').split())


def choose_page(pages: list[CommonsPage], query: str) -> CommonsPage:
    """Never return an image whose title has no search-word overlap."""
    query_words = set(query.lower().split())
    relevant = [
        page
        for page in pages
        if is_usable(page) and query_words.intersection(_title_words(page))
    ]
    if not relevant:
        raise ValueError('No usable Commons image found')
    return max(
        relevant,
        key=lambda page: len(query_words.intersection(_title_words(page))),
    )
