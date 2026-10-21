"""Probe and validate real media using typed FFprobe metadata."""

import hashlib
from pathlib import Path

from meme_generator.infrastructure.media.ffprobe import inspect_media
from meme_generator.infrastructure.media.metadata import MediaInfo

MAX_MEDIA_BYTES = 52_428_800
MIN_DURATION_SECONDS = 0.1
MAX_DURATION_SECONDS = 60.0


def probe_media(path: Path) -> MediaInfo:
    """Inspect the actual file rather than trusting its extension."""
    media: MediaInfo = inspect_media(path)
    media.get_stream('video')
    media.get_stream('audio')
    duration = media.format.duration
    if not MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS:
        raise ValueError('Clip duration must be between 0.1 and 60 seconds')
    return media


def verify_normalized(path: Path) -> MediaInfo:
    """Validate final codec, size, and FPS and return probed metadata."""
    media = probe_media(path)
    video = media.get_stream('video')
    audio = media.get_stream('audio')
    expected_video = ('h264', 1280, 720, '30/1')
    actual_video = (
        video.codec_name,
        video.width,
        video.height,
        video.avg_frame_rate,
    )
    if actual_video != expected_video or audio.codec_name != 'aac':
        raise ValueError(f'Unexpected output media format: {path}')
    return media


def check_source(path: Path, sha256: str | None) -> None:
    """Reject oversized, damaged, or unexpectedly changed input files."""
    if path.stat().st_size > MAX_MEDIA_BYTES:
        raise ValueError(f'Source clip exceeds the size limit: {path}')
    if sha256 is not None:
        with path.open('rb') as source:
            checksum = hashlib.file_digest(source, 'sha256').hexdigest()
        if checksum != sha256:
            raise ValueError(f'Source checksum mismatch: {path}')
    probe_media(path)
