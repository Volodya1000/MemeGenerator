"""Generate a temporary playable video with a curated real reaction."""

import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.persistence.in_memory import (
    InMemoryMemeRepository,
)
from meme_generator.infrastructure.media_probe import probe_clip

CATALOG = Path('assets/catalog.json')
LOGGER = logging.getLogger(__name__)


def create_context_image(directory: Path) -> None:
    """Make a synthetic context picture; no image hosting required."""
    directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-loglevel',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=blue:s=320x240',
            '-frames:v',
            '1',
            str(directory / '1.png'),
        ],
        capture_output=True,
        check=True,
    )


def verify_generated_video(output: Path) -> None:
    """Require playable audio and published provenance metadata."""
    media = probe_clip(output)
    if not media.has_audio or media.duration_seconds <= 1:
        raise ValueError('Real video output lacks expected streams')
    if not output.with_suffix('.scenario.json').is_file():
        raise FileNotFoundError('Scenario manifest was not published')
    if not output.with_suffix('.attribution.json').is_file():
        raise FileNotFoundError('Attribution manifest was not published')
    LOGGER.info('REAL_VIDEO_E2E_VERIFIED duration=%s', media.duration_seconds)


def main() -> None:
    """Produce no permanent media: test everything in a temporary folder."""
    with TemporaryDirectory(prefix='memegen-real-e2e-') as temporary:
        workspace = Path(temporary)
        create_context_image(workspace)
        output = workspace / 'demo.mp4'
        GenerationPipeline(
            catalog=InMemoryMemeRepository.from_json(CATALOG),
            planner=DemoPlanner(),
            image_provider=LocalImageProvider(workspace),
            renderer=FFmpegRenderer(),
        ).generate('Curated reaction demo', 1, output)
        verify_generated_video(output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
