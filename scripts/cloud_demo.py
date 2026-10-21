"""Produce an entirely synthetic, downloadable CI demonstration video."""

import logging
import subprocess
from pathlib import Path

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.meme_sources import MemeSource, MemeSources
from meme_generator.infrastructure.assets.catalog_importer import (
    import_catalog,
)
from meme_generator.infrastructure.ffmpeg.demo_context import (
    create_demo_context,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from meme_generator.infrastructure.media_probe import probe_clip

WORKSPACE = Path('output/cloud-demo-fixtures')
OUTPUT = Path('output/cloud-demo.mp4')
MEME_ID = 'synthetic_reaction'
SCENE_COUNT = 2
LOGGER = logging.getLogger(__name__)


def create_synthetic_clip(destination: Path) -> None:
    """Create a short reaction without copying third-party content."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-nostdin',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=purple:s=320x240:r=25:d=1.4',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=550:sample_rate=44100:duration=1.4',
            '-shortest',
            '-c:v',
            'mpeg4',
            '-c:a',
            'aac',
            str(destination),
        ],
        capture_output=True,
        check=True,
        text=True,
    )


def prepare_catalog() -> Path:
    """Import an owned synthetic source through the real asset importer."""
    raw = WORKSPACE / 'assets/raw' / f'{MEME_ID}.mp4'
    create_synthetic_clip(raw)
    manifest = WORKSPACE / 'assets/sources.json'
    sources = MemeSources(
        schema_version=1,
        clips=[
            MemeSource(
                meme_id=MEME_ID,
                phrase='Synthetic reaction',
                source_page='https://example.org/synthetic-reaction',
            ),
        ],
    )
    manifest.write_text(sources.model_dump_json(indent=2), encoding='utf-8')
    import_catalog(manifest, WORKSPACE)
    return WORKSPACE / 'assets/catalog.json'


def generate_demo(catalog: Path) -> None:
    """Render two scenes with the production pipeline and local images."""
    images = WORKSPACE / 'images'
    for index in range(1, SCENE_COUNT + 1):
        create_demo_context(images / f'{index}.png')
    GenerationPipeline(
        catalog=InMemoryMemeRepository.from_json(catalog),
        planner=DemoPlanner(),
        image_provider=LocalImageProvider(images),
        renderer=FFmpegRenderer(),
    ).generate('Cloud acceptance', SCENE_COUNT, OUTPUT)


def verify_demo() -> None:
    """Check that the downloadable artifact has valid video and metadata."""
    media = probe_clip(OUTPUT)
    expected = (
        OUTPUT,
        OUTPUT.with_suffix('.scenario.json'),
        OUTPUT.with_suffix('.attribution.json'),
    )
    if not media.has_audio or media.duration_seconds <= 1:
        raise ValueError('Generated video does not contain playable audio')
    if not all(path.is_file() for path in expected):
        raise FileNotFoundError('Demo output is incomplete')
    LOGGER.info('SYNTHETIC_VIDEO_READY=%s', OUTPUT)
    LOGGER.info('DURATION_SECONDS=%s', media.duration_seconds)


def main() -> None:
    """Create an independently redistributable acceptance artifact."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    generate_demo(prepare_catalog())
    verify_demo()


if __name__ == '__main__':
    main()
