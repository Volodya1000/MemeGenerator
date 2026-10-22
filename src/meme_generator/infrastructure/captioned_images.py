"""Render a readable caption over a previously acquired real photograph."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.caption_cards import (
    CARD_SIZE,
    FONT_NAME,
)

CAPTION_FONT_SIZES = (50, 44, 38, 32, 26)
MAX_CAPTION_LINES = 3
MAX_CAPTION_WIDTH = 1020
CAPTION_BAND = (58, 465, 1222, 684)
CAPTION_LEFT = 115
CAPTION_RADIUS = 25
CAPTION_LABEL_SIZE = 27
CAPTION_LINE_GAP = 10
CAPTION_BODY_TOP = 530
CAPTION_BOTTOM_PADDING = 20
CAPTION_BODY_BOTTOM = CAPTION_BAND[3] - CAPTION_BOTTOM_PADDING


def _wrap_text(
    caption: str,
    drawing: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
) -> list[str]:
    """Wrap whole words without allowing any to exceed the caption width."""
    lines: list[str] = []
    current = ''
    for word in caption.split():
        candidate = ' '.join(filter(None, (current, word)))
        if (
            drawing.textbbox((0, 0), candidate, font=font)[2]
            <= MAX_CAPTION_WIDTH
        ):
            current = candidate
            continue
        if drawing.textbbox((0, 0), word, font=font)[2] > MAX_CAPTION_WIDTH:
            raise ValueError('One caption word exceeds the photo width')
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def _caption_start(
    lines: list[str],
    drawing: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
) -> int | None:
    """Center the block vertically when all glyphs fit inside the band."""
    line_height: int = max(
        int(drawing.textbbox((0, 0), line, font=font, anchor='lt')[3])
        for line in lines
    )
    block_height = (len(lines) - 1) * (
        int(font.size) + CAPTION_LINE_GAP
    ) + line_height
    available_height = CAPTION_BODY_BOTTOM - CAPTION_BODY_TOP
    if block_height > available_height:
        return None
    return CAPTION_BODY_TOP + (available_height - block_height) // 2


def _caption_layout(
    caption: str,
    drawing: ImageDraw.ImageDraw,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Select a readable font that fits the actual drawable body area."""
    for size in CAPTION_FONT_SIZES:
        font = ImageFont.truetype(FONT_NAME, size)
        lines = _wrap_text(caption, drawing, font)
        if len(lines) > MAX_CAPTION_LINES:
            continue
        start_y = _caption_start(lines, drawing, font)
        if start_y is not None:
            return font, lines, start_y
    raise ValueError('Caption does not fit inside the photo caption area')


def _paint_caption(canvas: Image.Image, caption: str, order: int) -> None:
    """Draw a translucent readable label and situation over the photo."""
    drawing = ImageDraw.Draw(canvas, 'RGBA')
    drawing.rounded_rectangle(
        CAPTION_BAND,
        radius=CAPTION_RADIUS,
        fill=(10, 17, 29, 220),
    )
    label_font = ImageFont.truetype(FONT_NAME, CAPTION_LABEL_SIZE)
    drawing.text(
        (CAPTION_LEFT, 489),
        f'СИТУАЦИЯ {order}',
        font=label_font,
        fill='#A8E8F9',
    )
    _paint_lines(drawing, caption)


def _paint_lines(drawing: ImageDraw.ImageDraw, caption: str) -> None:
    """Keep the visible situation within the photographic label."""
    font, lines, start_y = _caption_layout(caption, drawing)
    for index, line in enumerate(lines):
        drawing.text(
            (
                CAPTION_LEFT,
                start_y + index * (int(font.size) + CAPTION_LINE_GAP),
            ),
            line,
            font=font,
            anchor='lt',
            fill='white',
        )


def add_caption(source: Path, caption: str, order: int, output: Path) -> None:
    """Combine a real downloaded photo and the visible Russian situation."""
    if not caption.strip():
        raise ValueError('Photo caption cannot be empty')
    with Image.open(source) as image:
        canvas = ImageOps.fit(image.convert('RGB'), CARD_SIZE)
    _paint_caption(canvas, caption, order)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format='PNG')


class CaptionedImageProvider(ImageProviderProtocol):
    """Decorate genuine searched photographs with a visible caption."""

    def __init__(self, source: ImageProviderProtocol) -> None:
        """Reuse any provider of attributable existing images."""
        self._source = source

    def fetch(self, scene: Scene, output_dir: Path) -> ImageAsset:
        """Preserve the source metadata while adding the situation caption."""
        original = self._source.fetch(scene, output_dir)
        destination = output_dir / f'{scene.order}-caption.png'
        add_caption(
            original.image_path, scene.description, scene.order, destination
        )
        return original.model_copy(update={'image_path': destination})
