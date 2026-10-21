"""Generate a temporary playable video with a curated real reaction."""

import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.scenario import Scenario
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import (
    InMemoryMemeRepository,
)

CATALOG = Path('assets/catalog.json')
LOGGER = logging.getLogger(__name__)
SCENE_COUNT = 3


def create_context_image(directory: Path, position: int) -> None:
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
            str(directory / f'{position}.png'),
        ],
        capture_output=True,
        check=True,
    )


def verify_generated_video(output: Path) -> None:
    """Require playable audio and published provenance metadata."""
    media = probe_clip(output)
    if not media.has_audio or media.duration_seconds <= SCENE_COUNT * 2:
        raise ValueError('Real video output lacks expected streams')
    if not all(
        path.is_file()
        for path in (
            output.with_suffix('.scenario.json'),
            output.with_suffix('.attribution.json'),
        )
    ):
        raise FileNotFoundError('Scenario and attribution must be published')
    scenario = Scenario.model_validate_json(
        output.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    chosen = {scene.meme_id for scene in scenario.scenes}
    if len(chosen) != SCENE_COUNT or len(scenario.scenes) != SCENE_COUNT:
        raise ValueError('Real preview must include three distinct reactions')
    LOGGER.info(
        'REAL_VIDEO_E2E_VERIFIED scenes=%s duration=%s',
        len(scenario.scenes),
        media.duration_seconds,
    )


def main() -> None:
    """Produce no permanent media: test everything in a temporary folder."""
    with TemporaryDirectory(prefix='memegen-real-e2e-') as temporary:
        workspace = Path(temporary)
        for position in range(1, SCENE_COUNT + 1):
            create_context_image(workspace, position)
        output = workspace / 'demo.mp4'
        GenerationPipeline(
            catalog=InMemoryMemeRepository.from_json(CATALOG),
            planner=DemoPlanner(),
            image_provider=LocalImageProvider(workspace),
            renderer=FFmpegRenderer(),
        ).generate('Curated reaction demo', SCENE_COUNT, output)
        verify_generated_video(output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
