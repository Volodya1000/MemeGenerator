"""Normalize scene stills and source clips into compatible segments."""

from pathlib import Path

from meme_generator.infrastructure.ffmpeg.command import execute_ffmpeg
from meme_generator.infrastructure.ffmpeg.settings import (
    FRAMES_PER_SECOND,
    SAMPLE_RATE,
    VIDEO_FILTER,
)
from meme_generator.infrastructure.media_probe import probe_clip

INPUT_FLAG = '-i'
MAP_FLAG = '-map'


def render_image(source: Path, target: Path, duration_seconds: int) -> None:
    """Encode a static context image as a short H.264/AAC segment."""
    execute_ffmpeg(
        [
            '-loop',
            '1',
            '-framerate',
            str(FRAMES_PER_SECOND),
            INPUT_FLAG,
            str(source),
            '-f',
            'lavfi',
            INPUT_FLAG,
            f'anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE}',
            '-t',
            str(duration_seconds),
            '-vf',
            VIDEO_FILTER,
            MAP_FLAG,
            '0:v:0',
            MAP_FLAG,
            '1:a:0',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-ar',
            str(SAMPLE_RATE),
            '-ac',
            '2',
            '-shortest',
            str(target),
        ]
    )


def render_clip(source: Path, target: Path) -> None:
    """Normalize an existing reaction clip, adding silent audio if absent."""
    metadata = probe_clip(source)
    arguments = [INPUT_FLAG, str(source)]
    if not metadata.has_audio:
        arguments.extend(
            [
                '-f',
                'lavfi',
                INPUT_FLAG,
                f'anullsrc=channel_layout=stereo:sample_rate={SAMPLE_RATE}',
            ]
        )
    audio_input = '0:a:0' if metadata.has_audio else '1:a:0'
    execute_ffmpeg(
        [
            *arguments,
            MAP_FLAG,
            '0:v:0',
            MAP_FLAG,
            audio_input,
            '-vf',
            VIDEO_FILTER,
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-ar',
            str(SAMPLE_RATE),
            '-ac',
            '2',
            '-shortest',
            str(target),
        ]
    )
