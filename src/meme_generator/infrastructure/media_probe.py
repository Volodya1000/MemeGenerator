"""Use ffprobe to verify real media streams before expensive renders."""

import json
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class ClipInfo(BaseModel):
    """Duration and streams provided by FFprobe."""

    duration_seconds: float = Field(gt=0)
    has_audio: bool


def probe_clip(path: Path) -> ClipInfo:
    """Reject unreadable clips and media without video streams."""
    command = [
        'ffprobe',
        '-v',
        'error',
        '-show_streams',
        '-show_format',
        '-of',
        'json',
        str(path),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    streams = payload['streams']
    if not any(stream['codec_type'] == 'video' for stream in streams):
        raise ValueError('Clip must contain a video stream')
    duration = float(payload['format']['duration'])
    return ClipInfo(
        duration_seconds=duration,
        has_audio=any(stream['codec_type'] == 'audio' for stream in streams),
    )
