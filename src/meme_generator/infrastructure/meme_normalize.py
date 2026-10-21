"""Normalize reaction clips using FFmpeg without partial output files."""

import subprocess
import tempfile
from pathlib import Path

from meme_generator.infrastructure.meme_probe import verify_normalized

VIDEO_FILTER = (
    'scale=1280:720:force_original_aspect_ratio=decrease,'
    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p'
)
AUDIO_FILTER = 'loudnorm=I=-16:TP=-1.5:LRA=11'


def normalize_media(source: Path, destination: Path) -> None:
    """Convert a short reaction into predictable H.264/AAC MP4."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
        temporary = Path(directory) / 'normalized.mp4'
        command = (
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
            '-i', str(source), '-map', '0:v:0', '-map', '0:a:0',
            '-vf', VIDEO_FILTER, '-af', AUDIO_FILTER,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
            '-movflags', '+faststart', str(temporary),
        )
        subprocess.run(command, check=True, capture_output=True, text=True)
        verify_normalized(temporary)
        temporary.replace(destination)
