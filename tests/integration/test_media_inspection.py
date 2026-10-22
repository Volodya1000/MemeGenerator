"""Behavior of shared media inspection with real local FFmpeg media."""

import subprocess
from pathlib import Path

import pytest

from meme_generator.infrastructure.assets.probe import probe_media
from meme_generator.infrastructure.media_probe import probe_clip


def create_synthetic_video(path: Path, *, with_audio: bool) -> None:
    """Produce tiny video with or without a real sound stream."""
    command: list[str] = [
        'ffmpeg',
        '-loglevel',
        'error',
        '-nostdin',
        '-y',
        '-f',
        'lavfi',
        '-i',
        'color=c=black:s=160x120:r=25',
    ]
    if with_audio:
        command.extend(
            (
                '-f',
                'lavfi',
                '-i',
                'sine=frequency=440:sample_rate=44100',
            )
        )
    command.extend(('-t', '0.4', '-c:v', 'mpeg4'))
    if with_audio:
        command.extend(('-c:a', 'aac'))
    command.append(str(path))
    subprocess.run(command, check=True, capture_output=True, text=True)


@pytest.mark.integration
def test_renderer_accepts_silent_video(tmp_path: Path) -> None:
    """The renderer can add silence to a video missing an audio stream."""
    source = tmp_path / 'silent.mp4'
    create_synthetic_video(source, with_audio=False)

    clip = probe_clip(source)
    assert clip.duration_seconds > 0
    assert not clip.has_audio
    with pytest.raises(ValueError, match='audio'):
        probe_media(source)


@pytest.mark.integration
def test_catalog_import_accepts_video_with_audio(tmp_path: Path) -> None:
    """Imported reaction clips must provide an audio stream."""
    source = tmp_path / 'reaction.mp4'
    create_synthetic_video(source, with_audio=True)

    clip = probe_clip(source)
    assert clip.duration_seconds > 0
    assert clip.has_audio
    assert probe_media(source).get_stream('audio').codec_type == 'audio'


@pytest.mark.integration
def test_media_inspection_rejects_audio_only_file(tmp_path: Path) -> None:
    """A playable audio-only recording is not accepted as reaction video."""
    source = tmp_path / 'recording.wav'
    subprocess.run(
        (
            'ffmpeg',
            '-loglevel',
            'error',
            '-nostdin',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=0.4',
            str(source),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    with pytest.raises(ValueError, match='video'):
        probe_clip(source)
    with pytest.raises(ValueError, match='video'):
        probe_media(source)
