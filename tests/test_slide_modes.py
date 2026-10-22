"""Test the observable differences between the three slide modes."""

from pathlib import Path

import pytest
from PIL import Image, ImageChops

from meme_generator.composition.images import create_images
from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.domain.slide_mode import SlideMode
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.captioned_images import (
    CaptionedImageProvider,
    add_caption,
)

TEST_IMAGE_SIZE = (1280, 720)


def test_only_text_ignores_remote_image_search() -> None:
    """A text slide never requires a Commons HTTP request."""
    settings = GenerationSettings(
        slide_mode=SlideMode.TEXT_ONLY,
        images='commons',
    )
    assert isinstance(create_images(settings), CaptionCardImageProvider)


def test_only_image_uses_a_local_photo(tmp_path: Path) -> None:
    """The photo-only mode preserves an existing user supplied photo."""
    settings = GenerationSettings(
        slide_mode=SlideMode.IMAGE_ONLY,
        images='local',
        image_dir=tmp_path,
    )
    Image.new('RGB', TEST_IMAGE_SIZE, 'red').save(tmp_path / '1.png')
    scene = Scene(
        order=1,
        description='Машина сломалась',
        image_query='broken down car',
        meme_id='reaction',
    )
    asset: ImageAsset = create_images(settings).fetch(
        scene, tmp_path / 'output'
    )
    with Image.open(asset.image_path) as image:
        assert image.getpixel((100, 100)) == (255, 0, 0)


def test_image_with_caption_produces_overlay(tmp_path: Path) -> None:
    """Russian text visibly changes the image while keeping its base photo."""
    source = tmp_path / 'source.png'
    output = tmp_path / 'caption.png'
    Image.new('RGB', TEST_IMAGE_SIZE, 'red').save(source)
    add_caption(source, 'Когда купил машину. Она сломалась', 1, output)
    with Image.open(source) as image, Image.open(output) as captioned:
        assert captioned.size == TEST_IMAGE_SIZE
        assert ImageChops.difference(image, captioned).getbbox() is not None
        assert captioned.getpixel((100, 100)) == image.getpixel((100, 100))


def test_photo_modes_reject_text_source() -> None:
    """A mismatched UI combination is rejected before rendering."""
    with pytest.raises(ValueError, match='commons or local'):
        create_images(
            GenerationSettings(
                slide_mode=SlideMode.IMAGE_WITH_CAPTION,
                images='cards',
            )
        )


def test_caption_preserves_source_attribution(tmp_path: Path) -> None:
    """The overlay does not erase the original photo's source or license."""
    images = tmp_path / 'images'
    images.mkdir()
    Image.new('RGB', TEST_IMAGE_SIZE, 'green').save(images / '1.png')
    settings = GenerationSettings(
        slide_mode=SlideMode.IMAGE_WITH_CAPTION,
        images='local',
        image_dir=images,
    )
    provider = create_images(settings)
    assert isinstance(provider, CaptionedImageProvider)
    scene = Scene(
        order=1,
        description='Когда покупка оказалась неудачной',
        image_query='broken car',
        meme_id='reaction',
    )
    generated = provider.fetch(scene, tmp_path / 'out')
    assert generated.image_path.is_file()
    assert generated.license_name == 'User-provided'
    assert generated.image_path.suffix == '.png'


def test_long_photo_caption_stays_clear_of_heading(tmp_path: Path) -> None:
    """Visible heading and long body never collide or leave the caption band."""
    source = tmp_path / 'original.png'
    output = tmp_path / 'captioned.png'
    Image.new('RGB', TEST_IMAGE_SIZE, 'red').save(source)
    description = (
        'Счастливый владелец только что купил '
        'подержанную машину и едет по городу.'
    )
    add_caption(source, description, 1, output)
    with Image.open(output) as rendered:
        heading_rows: list[int] = []
        body_rows: list[int] = []
        for vertical in range(465, 684):
            row_pixels = [
                rendered.getpixel((horizontal, vertical))
                for horizontal in range(115, 1190)
            ]
            if (168, 232, 249) in row_pixels:
                heading_rows.append(vertical)
            if (255, 255, 255) in row_pixels:
                body_rows.append(vertical)
    assert heading_rows
    assert body_rows
    assert max(heading_rows) + 10 < min(body_rows)
    assert max(body_rows) < 664


def test_photo_caption_rejects_unrenderable_text(tmp_path: Path) -> None:
    """Unrenderable descriptions fail rather than silently overlap labels."""
    source = tmp_path / 'source.png'
    Image.new('RGB', TEST_IMAGE_SIZE, 'red').save(source)
    with pytest.raises(ValueError, match='exceeds the photo width'):
        add_caption(source, 'я' * 200, 1, tmp_path / 'out.png')
