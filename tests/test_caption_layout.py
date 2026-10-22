"""Behavioral checks for photo captions, separated from slide-mode tests."""

from pathlib import Path

import pytest
from PIL import Image

from meme_generator.infrastructure.captioned_images import (
    CAPTION_BAND,
    CAPTION_BODY_BOTTOM,
    CAPTION_LEFT,
    add_caption,
)

FRAME_SIZE = (1280, 720)
HEADING_COLOR = (168, 232, 249)
TEXT_COLOR = (255, 255, 255)
LONG_WORD_LENGTH = 200


def _colored_rows(
    rendered: Image.Image,
    expected: tuple[int, int, int],
) -> list[int]:
    """Locate visible text pixels in the caption strip."""
    return [
        vertical
        for vertical in range(CAPTION_BAND[1], CAPTION_BAND[3])
        if any(
            rendered.getpixel((horizontal, vertical)) == expected
            for horizontal in range(CAPTION_LEFT, CAPTION_BAND[2])
        )
    ]


def test_long_caption_has_separate_heading(tmp_path: Path) -> None:
    """Heading and complete body stay separated inside the photo band."""
    source = tmp_path / 'original.png'
    output = tmp_path / 'captioned.png'
    Image.new('RGB', FRAME_SIZE, 'red').save(source)
    add_caption(
        source,
        'Счастливый владелец только что купил '
        'подержанную машину и едет по городу.',
        1,
        output,
    )
    with Image.open(output) as rendered:
        heading_rows = _colored_rows(rendered, HEADING_COLOR)
        body_rows = _colored_rows(rendered, TEXT_COLOR)
    assert heading_rows
    assert body_rows
    assert max(heading_rows) + 10 < min(body_rows)
    assert max(body_rows) < CAPTION_BODY_BOTTOM


def test_photo_caption_rejects_unrenderable_text(tmp_path: Path) -> None:
    """Unrenderable descriptions fail rather than overlap the label."""
    source = tmp_path / 'source.png'
    Image.new('RGB', FRAME_SIZE, 'red').save(source)
    with pytest.raises(ValueError, match='exceeds the photo width'):
        add_caption(source, 'я' * LONG_WORD_LENGTH, 1, tmp_path / 'out.png')
