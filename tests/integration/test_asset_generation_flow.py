"""Full real-code path: synthetic media import -> catalog -> rendered MP4."""

import json
import subprocess
from pathlib import Path

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.infrastructure.assets.catalog_importer import (
    import_catalog,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from meme_generator.infrastructure.media_probe import probe_clip

MEME_ID = 'approved_reaction'
ENCODING = 'utf-8'


def prepare_clip(project: Path) -> None:
    """Create an authorized synthetic reaction with real audio and video."""
    raw = project / 'assets' / 'raw' / f'{MEME_ID}.mp4'
    raw.parent.mkdir(parents=True)
    subprocess.run(
        [
            'ffmpeg',
            '-loglevel',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=red:s=320x240:r=25',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=0.6',
            '-t',
            '0.6',
            '-c:v',
            'mpeg4',
            '-c:a',
            'aac',
            str(raw),
        ],
        capture_output=True,
        check=True,
    )


def prepare_image(project: Path) -> Path:
    """Create a real context image to feed the local image provider."""
    directory = project / 'images'
    directory.mkdir()
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
    return directory


def prepare_manifest(project: Path) -> Path:
    """Supply exactly one synthetic, locally-owned reaction source."""
    source = project / 'sources.json'
    source.write_text(
        json.dumps(
            {
                'schema_version': 1,
                'clips': [
                    {
                        'meme_id': MEME_ID,
                        'phrase': 'Agreed',
                        'source_page': 'https://example.org/reaction',
                    }
                ],
            }
        ),
        encoding=ENCODING,
    )
    return source


def test_imported_asset_generates_playable_video(tmp_path: Path) -> None:
    """Import a clip, then generate a full video from the catalog."""
    prepare_clip(tmp_path)
    images = prepare_image(tmp_path)
    import_catalog(prepare_manifest(tmp_path), tmp_path)
    repository = InMemoryMemeRepository.from_json(
        tmp_path / 'assets' / 'catalog.json'
    )
    assert repository.get(MEME_ID).video_path.is_file()
    output = tmp_path / 'output' / 'complete.mp4'
    GenerationPipeline(
        catalog=repository,
        planner=DemoPlanner(),
        image_provider=LocalImageProvider(images),
        renderer=FFmpegRenderer(),
    ).generate('Integration test', 1, output)
    assert probe_clip(output).has_audio
    assert output.with_suffix('.scenario.json').is_file()
    assert output.with_suffix('.attribution.json').is_file()
