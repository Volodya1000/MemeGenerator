"""Rank eligible Wikimedia Commons search results."""

from meme_generator.infrastructure.commons.models import CommonsPage

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 360
SEARCH_LIMIT = 15
SEARCH_IMAGE_WIDTH = 1280
SUPPORTED_MIME = frozenset(('image/jpeg', 'image/png', 'image/webp'))


def search_parameters(query: str) -> dict[str, str | int]:
    """Search image files with sufficient resolution and attribution."""
    return {
        'action': 'query',
        'format': 'json',
        'generator': 'search',
        'gsrsearch': query,
        'gsrnamespace': 6,
        'gsrlimit': SEARCH_LIMIT,
        'prop': 'imageinfo',
        'iiprop': 'url|size|mime|extmetadata',
        'iiurlwidth': SEARCH_IMAGE_WIDTH,
    }


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


def choose_page(pages: list[CommonsPage], query: str) -> CommonsPage:
    """Select the most relevant eligible image by title overlap."""
    relevant = [page for page in pages if is_usable(page)]
    if not relevant:
        raise ValueError('No usable Commons image found')
    query_words = set(query.lower().split())
    return max(
        relevant,
        key=lambda page: len(
            query_words.intersection(
                set(page.title.lower().replace('_', ' ').split())
            )
        ),
    )
