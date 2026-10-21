"""Create a story-driven synthetic preview with truthful reaction labels."""

import logging
import subprocess
from pathlib import Path

from cloud_story import PreviewPlanner, STORY

from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.meme_sources import MemeSource, MemeSources
from meme_generator.infrastructure.assets.catalog_importer import (
    import_catalog,
)
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
    render_caption,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from meme_generator.infrastructure.media_probe import probe_clip

WORKSPACE = Path('output/cloud-demo-fixtures')
OUTPUT = Path('output/cloud-demo.mp4')
LOGGER = logging.getLogger(__name__)
def create_synthetic_clip(
    destination: Path,
    phrase: str,
    variation: int,
) -> None:
    """Generate a clearly labelled imitation with silence, not a fake voice."""
    image = destination.with_suffix('.png')
    render_caption(
        phrase,
        image,
        label='ТЕКСТОВАЯ ЗАГЛУШКА РЕАКЦИИ',
        variation=variation + 1,
    )
    subprocess.run(
        [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-nostdin',
            '-y',
            '-loop',
            '1',
            '-framerate',
            '30',
            '-i',
            str(image),
            '-f',
            'lavfi',
            '-i',
            'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-t',
            '1.8',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-shortest',
            str(destination),
        ],
        capture_output=True,
        check=True,
        text=True,
    )


def preview_sources() -> list[MemeSource]:
    """Build the synthetic catalog from the scripted reaction references."""
    return [
        MemeSource(
            meme_id=identifier,
            phrase=phrase,
            source_page='https://example.org/original-demo-media',
        )
        for identifier, phrase, _ in STORY
    ]


def prepare_catalog() -> Path:
    """Import the three synthetic clips through the production importer."""
    raw = WORKSPACE / 'assets/raw'
    clips = preview_sources()
    for index, clip in enumerate(clips, start=1):
        create_synthetic_clip(
            raw / f'{clip.meme_id}.mp4', clip.phrase, index
        )
    manifest = WORKSPACE / 'assets/sources.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        MemeSources(schema_version=1, clips=clips).model_dump_json(indent=2),
        encoding='utf-8',
    )
    import_catalog(manifest, WORKSPACE)
    return WORKSPACE / 'assets/catalog.json'


def generate_demo(catalog: Path) -> None:
    """Use the production renderer with three contextual caption cards."""
    GenerationPipeline(
        catalog=InMemoryMemeRepository.from_json(catalog),
        planner=PreviewPlanner(),
        image_provider=CaptionCardImageProvider(),
        renderer=FFmpegRenderer(),
    ).generate('Жизнь разработчика', len(STORY), OUTPUT)


def verify_demo() -> None:
    """Validate the video and its three distinct, ordered real pipeline scenes."""
    media = probe_clip(OUTPUT)
    if not media.has_audio or media.duration_seconds <= 8:
        raise ValueError('Generated preview lacks expected audio or scenes')
    if not OUTPUT.with_suffix('.attribution.json').is_file():
        raise FileNotFoundError('Attribution manifest is missing')
    scenario = Scenario.model_validate_json(
        OUTPUT.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    expected_ids = [identifier for identifier, _, _ in STORY]
    if [scene.meme_id for scene in scenario.scenes] != expected_ids:
        raise ValueError('Preview scene sequence does not match the script')
    LOGGER.info('MEANINGFUL_PREVIEW=%s', OUTPUT)
    LOGGER.info('SCENES=%s DURATION=%s', len(STORY), media.duration_seconds)


def main() -> None:
    """Create a shareable preview without third-party clips or invented voice."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    generate_demo(prepare_catalog())
    verify_demo()


if __name__ == '__main__':
    main()
