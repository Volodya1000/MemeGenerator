"""Safely invoke FFmpeg as a subprocess without a shell."""

import subprocess


def execute_ffmpeg(arguments: list[str]) -> None:
    """Treat all user paths as literal arguments, never shell fragments."""
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
