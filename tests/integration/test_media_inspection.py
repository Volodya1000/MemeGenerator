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
@pytest.mark.parametrize('with_audio', (False, True))
def test_media_inspection_preserves_audio_policy(
    tmp_path: Path,
    with_audio: bool,
) -> None:
    """Rendering allows silent video while catalog import requires audio."""
    source = tmp_path / 'source.mp4'
    create_synthetic_video(source, with_audio=with_audio)

    clip = probe_clip(source)
    assert clip.duration_seconds > 0
    assert clip.has_audio is with_audio

    if with_audio:
        assert probe_media(source).get_stream('audio').codec_type == 'audio'
    else:
        with pytest.raises(ValueError, match='audio'):
            probe_media(source)


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
