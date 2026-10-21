"""Behavioral acceptance tests for readable offline caption cards."""

from pathlib import Path

import pytest
from PIL import Image

from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
    render_caption,
)


def test_generated_caption_is_a_real_full_hd_ready_image(
    tmp_path: Path,
) -> None:
    """A contextual sentence produces a readable, nonuniform image."""
    asset = CaptionCardImageProvider().fetch(
        'Когда CI наконец стал зелёным', 1, tmp_path
    )
    with Image.open(asset.image_path) as image:
        assert image.size == (1280, 720)
        assert len(image.getcolors(maxcolors=1_000_000) or []) > 2
    assert asset.license_name == 'Original generated typography'


def test_long_caption_wraps_instead_of_being_truncated(
    tmp_path: Path,
) -> None:
    """Multiple full words remain representable without cropping the card."""
    caption = (
        'Когда тебе сказали поправить одну строчку '
        'а в итоге пришлось переписать половину генератора'
    )
    output = tmp_path / 'long.png'
    render_caption(caption, output, label='ПРОВЕРКА', variation=2)
    with Image.open(output) as image:
        assert image.size == (1280, 720)


def test_blank_caption_is_rejected(tmp_path: Path) -> None:
    """An empty card must not silently become another blue rectangle."""
    with pytest.raises(ValueError):
        CaptionCardImageProvider().fetch('   ', 1, tmp_path)
