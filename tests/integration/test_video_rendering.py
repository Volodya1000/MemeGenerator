"""Render synthetic media to verify the FFmpeg montage contract."""

import shutil
import subprocess
from pathlib import Path

import pytest

from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.media_probe import probe_clip


def synthetic_media(directory: Path) -> tuple[Path, Path]:
    """Create non-copyrighted still and reaction test fixtures."""
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
    """A complete MP4 contains images, reactions, and audio."""
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
        InMemoryMemeRepository(
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
