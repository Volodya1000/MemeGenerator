"""Read validated media metadata at the FFprobe subprocess boundary."""

import subprocess
from pathlib import Path

from meme_generator.infrastructure.media.metadata import MediaInfo


def inspect_media(path: Path) -> MediaInfo:
    """Decode container and stream metadata through one typed FFprobe call."""
    command: tuple[str, ...] = (
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate',
        '-of',
        'json',
        str(path),
    )
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return MediaInfo.model_validate_json(completed.stdout)
