"""Render short synthetic video to verify the FFmpeg montage contract."""

import shutil
import subprocess
from pathlib import Path

import pytest

from meme_generator.domain.models import Meme, Scenario, Scene
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.images import ImageAsset
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.infrastructure.rendering import FFmpegRenderer


def synthetic_media(directory: Path) -> tuple[Path, Path]:
    """Create non-copyrighted still and recorded reaction test fixtures."""
    image = directory / 'context.png'
    clip = directory / 'reaction.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=blue:s=320x240:d=1',
            '-frames:v',
            '1',
            str(image),
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=red:s=320x240:d=1',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=1',
            '-shortest',
            '-c:v',
            'libx264',
            '-c:a',
            'aac',
            str(clip),
        ],
        capture_output=True,
        check=True,
    )
    return image, clip


@pytest.mark.skipif(
    shutil.which('ffmpeg') is None or shutil.which('ffprobe') is None,
    reason='FFmpeg and FFprobe required',
)
def test_video_contains_context_and_reaction(tmp_path: Path) -> None:
    """Both images and reaction clips produce a valid MP4 with audio."""
    image_path, clip_path = synthetic_media(tmp_path)
    scenario = Scenario(
        theme='An example',
        scenes=[
            Scene(
                order=1,
                description='Blue screen',
                image_query='blue square',
                meme_id='reaction',
            )
        ],
    )
    output_path = tmp_path / 'result.mp4'
    FFmpegRenderer().render(
        scenario,
        MemeCatalog(
            [
                Meme(meme_id='reaction', phrase='wow', video_path=clip_path),
            ]
        ),
        [
            ImageAsset(
                image_path=image_path,
                source_url='local',
                license_name='Test generated',
            )
        ],
        output_path,
    )
    metadata = probe_clip(output_path)
    assert metadata.has_audio
    assert int(metadata.duration_seconds) >= 2
