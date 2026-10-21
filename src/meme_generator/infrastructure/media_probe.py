"""Use typed FFprobe metadata to verify media before rendering."""

import subprocess
from pathlib import Path

from meme_generator.domain.clip_info import ClipInfo
from meme_generator.infrastructure.assets.media_models import MediaInfo


def probe_clip(path: Path) -> ClipInfo:
    """Reject unreadable clips and media without video streams."""
    command: list[str] = [
        'ffprobe',
        '-v',
        'error',
        '-show_streams',
        '-show_format',
        '-of',
        'json',
        str(path),
    ]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    media: MediaInfo = MediaInfo.model_validate_json(completed.stdout)
    media.get_stream('video')
    has_audio: bool = any(
        stream.codec_type == 'audio' for stream in media.streams
    )
    return ClipInfo(
        duration_seconds=media.format.duration,
        has_audio=has_audio,
    )
