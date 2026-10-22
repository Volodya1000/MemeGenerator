"""Verify the output actually contains frames from curated source clips."""

import io
import logging
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from real_review_story import REAL_STORY

from meme_generator.infrastructure.ffmpeg.settings import (
    IMAGE_DURATION_SECONDS,
)
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import InMemoryMemeRepository

CATALOG = Path('assets/catalog.json')
OUTPUT = Path('output/real-reactions-review.mp4')
FRAME_SIZE = (320, 180)
FRAME_SAMPLE_SECONDS = 0.75
MAX_PIXEL_DIFFERENCE = 30.0
LOGGER = logging.getLogger(__name__)


def _read_frame(video: Path, seconds: float) -> Image.Image:
    """Decode a real video frame rather than trusting the file extension."""
    result = subprocess.run(
        [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-ss', str(seconds), '-i', str(video),
            '-frames:v', '1', '-f', 'image2pipe',
            '-vcodec', 'png', '-',
        ],
        check=True,
        capture_output=True,
    )
    with Image.open(io.BytesIO(result.stdout)) as image:
        return image.convert('RGB').resize(FRAME_SIZE)


def _distance(output: Path, source: Path, start: float) -> float:
    """Measure whether the output reaction resembles its genuine source."""
    original = _read_frame(source, FRAME_SAMPLE_SECONDS)
    rendered = _read_frame(output, start + FRAME_SAMPLE_SECONDS)
    difference = ImageChops.difference(original, rendered)
    return sum(ImageStat.Stat(difference).mean) / 3


def verify_real_review_frames() -> None:
    """Ensure each scene embeds moving interview footage, not a text card."""
    catalog = InMemoryMemeRepository.from_json(CATALOG)
    position = 0.0
    for meme_id, _ in REAL_STORY:
        source = catalog.get(meme_id).video_path
        position += IMAGE_DURATION_SECONDS
        distance = _distance(OUTPUT, source, position)
        LOGGER.info('SOURCE_FRAME_MATCH %s distance=%.2f', meme_id, distance)
        if distance > MAX_PIXEL_DIFFERENCE:
            raise ValueError(f'Real source footage missing for {meme_id}')
        position += probe_clip(source).duration_seconds


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    verify_real_review_frames()
