"""Render readable offline situation cards without external image services."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scene import Scene

CARD_SIZE = (1280, 720)
TEXT_WIDTH = 1050
CARD_COLORS = ('#15284A', '#40254F', '#154B48', '#513628')
ACCENT_COLORS = ('#53D8FB', '#FF8CC6', '#FFE187', '#97F0D1')
FONT_NAME = 'DejaVuSans.ttf'
MAX_TEXT_LINES = 5
CARD_HEADING_SIZE = 32
CARD_CENTER_Y = 348
TEXT_SIZES = (76, 68, 60, 52, 44, 36)


def _break_lines(
    text: str,
    drawing: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
) -> list[str]:
    """Wrap complete words to fit the visible card width."""
    lines: list[str] = []
    current = ''
    for word in text.split():
        candidate = ' '.join(filter(None, (current, word)))
        bounds = drawing.textbbox((0, 0), candidate, font=font)
        if bounds[2] <= TEXT_WIDTH:
            current = candidate
        elif current:
            lines.append(current)
            current = word
        else:
            raise ValueError('One caption word is too wide to fit')
    if current:
        lines.append(current)
    return lines


def _fit_caption(
    text: str,
    drawing: ImageDraw.ImageDraw,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Choose a readable font size without truncating the caption."""
    for size in TEXT_SIZES:
        font = ImageFont.truetype(FONT_NAME, size)
        lines = _break_lines(text, drawing, font)
        if len(lines) <= MAX_TEXT_LINES:
            return font, lines
    raise ValueError('Caption is too long for the card')


def _draw_background(palette: int, label: str) -> Image.Image:
    """Paint a distinctive situation/reaction frame with an accent stripe."""
    canvas = Image.new('RGB', CARD_SIZE, CARD_COLORS[palette])
    drawing = ImageDraw.Draw(canvas)
    drawing.rounded_rectangle(
        (92, 92, 110, 627),
        radius=9,
        fill=ACCENT_COLORS[palette],
    )
    drawing.text(
        (155, 110),
        label,
        font=ImageFont.truetype(FONT_NAME, CARD_HEADING_SIZE),
        fill=ACCENT_COLORS[palette],
    )
    drawing.rounded_rectangle(
        (155, 623, 1080, 627),
        radius=2,
        fill=ACCENT_COLORS[palette],
    )
    return canvas


def _line_position(index: int, count: int, font_size: int) -> int:
    """Center complete lines vertically in the available text region."""
    line_height = font_size + 24
    return CARD_CENTER_Y - count * line_height // 2 + index * line_height


def _draw_caption(canvas: Image.Image, text: str) -> None:
    """Fit words into the safe caption region of the rendered image."""
    drawing = ImageDraw.Draw(canvas)
    font, lines = _fit_caption(text, drawing)
    for index, line in enumerate(lines):
        drawing.text(
            (155, _line_position(index, len(lines), int(font.size))),
            line,
            font=font,
            fill='#FFFFFF',
        )


def render_caption(
    text: str,
    destination: Path,
    *,
    label: str,
    variation: int,
) -> None:
    """Draw a legible 16:9 card and preserve all supplied words."""
    if not text.strip():
        raise ValueError('Card caption cannot be empty')
    palette = (variation - 1) % len(CARD_COLORS)
    canvas = _draw_background(palette, label)
    _draw_caption(canvas, text)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format='PNG')


class CaptionCardImageProvider:
    """Render the visible scene description, never its search query."""

    def fetch(
        self,
        scene: Scene,
        output_dir: Path,
    ) -> ImageAsset:
        """Generate a context card without network dependencies."""
        destination = output_dir / f'{scene.order}.png'
        render_caption(
            scene.description,
            destination,
            label=f'СИТУАЦИЯ {scene.order}',
            variation=scene.order,
        )
        return ImageAsset(
            image_path=destination,
            source_url=destination.resolve().as_uri(),
            license_name='Original generated typography',
        )
