"""FFmpeg integration checks based exclusively on synthetic video."""

import subprocess
from pathlib import Path

import pytest

from meme_generator.infrastructure.meme_media import (
    normalize_media,
    verify_normalized,
)


@pytest.mark.integration
def test_short_clip_is_normalized(tmp_path: Path) -> None:
    """Normalize a locally generated clip without accessing real memes."""
    original = tmp_path / 'source.mp4'
    destination = tmp_path / 'normalized.mp4'
    subprocess.run(
        (
            'ffmpeg', '-loglevel', 'error', '-nostdin', '-y',
            '-f', 'lavfi', '-i', 'color=c=blue:s=320x240:r=25',
            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100',
            '-t', '0.8', '-c:v', 'mpeg4', '-c:a', 'aac', str(original),
        ),
        check=True,
        capture_output=True,
    )
    normalize_media(original, destination)
    verify_normalized(destination)
    assert destination.stat().st_size > 0
