"""Typed FFprobe results and media validation for short reactions."""

import hashlib
import subprocess
from pathlib import Path

from pydantic import BaseModel

MAX_MEDIA_BYTES = 52_428_800
MIN_DURATION_SECONDS = 0.1
MAX_DURATION_SECONDS = 60.0


class MediaStream(BaseModel):
    """Relevant media stream properties reported by ffprobe."""

    codec_type: str
    codec_name: str | None = None
    width: int | None = None
    height: int | None = None
    avg_frame_rate: str | None = None


class MediaFormat(BaseModel):
    """Container properties returned by ffprobe."""

    duration: float


class MediaInfo(BaseModel):
    """Typed output of ffprobe's JSON writer."""

    streams: list[MediaStream]
    format: MediaFormat

    def get_stream(self, stream_type: str) -> MediaStream:
        """Require an audio or video stream in a usable clip."""
        for stream in self.streams:
            if stream.codec_type == stream_type:
                return stream
        raise ValueError(f'Media must contain a {stream_type} stream')


def probe_media(path: Path) -> MediaInfo:
    """Inspect the actual file rather than trusting its extension."""
    process = subprocess.run(
        (
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate',
            '-of', 'json', str(path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    media = MediaInfo.model_validate_json(process.stdout)
    media.get_stream('video')
    media.get_stream('audio')
    duration = media.format.duration
    if not MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS:
        raise ValueError('Clip duration must be between 0.1 and 60 seconds')
    return media


def verify_normalized(path: Path) -> None:
    """Check the codec, resolution, and frame rate of the final clip."""
    media = probe_media(path)
    video = media.get_stream('video')
    audio = media.get_stream('audio')
    expected_video = ('h264', 1280, 720, '30/1')
    actual_video = (
        video.codec_name, video.width, video.height, video.avg_frame_rate,
    )
    if actual_video != expected_video or audio.codec_name != 'aac':
        raise ValueError(f'Unexpected output media format: {path}')


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
