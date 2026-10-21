"""Generate an offline synthetic visual for local video smoke tests."""

from pathlib import Path

from meme_generator.infrastructure.ffmpeg.command import execute_ffmpeg


def create_demo_context(destination: Path) -> None:
    """Create a one-frame context image without internet or model access."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    execute_ffmpeg(
        [
            '-f',
            'lavfi',
            '-i',
            'color=c=steelblue:s=640x480',
            '-frames:v',
            '1',
            str(destination),
        ]
    )
