"""Deterministic Commons filtering and ranking without a network."""

import pytest

from meme_generator.infrastructure.commons.models import (
    CommonsImage,
    CommonsPage,
)
from meme_generator.infrastructure.commons.search import choose_page


IMAGE_WIDTH = 900
IMAGE_HEIGHT = 700


def sample_page(title: str, mime: str) -> CommonsPage:
    """Create a Commons result with sufficiently large dimensions."""
    return CommonsPage(
        title=title,
        imageinfo=[
            CommonsImage(
                url='https://upload.wikimedia.org/wikipedia/example.png',
                mime=mime,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT,
            )
        ],
    )


def test_search_prefers_relevant_image() -> None:
    """Title relevance influences selection among valid images."""
    other = sample_page('other animal', 'image/png')
    relevant = sample_page('developer broken tests', 'image/png')
    assert choose_page([other, relevant], 'broken tests') == relevant


def test_search_rejects_svg() -> None:
    """A vector asset must not enter the raster-image renderer."""
    page = sample_page('broken tests', 'image/svg+xml')
    with pytest.raises(ValueError, match='No usable'):
        choose_page([page], 'broken tests')
