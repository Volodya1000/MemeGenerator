"""Bounded media download, probing, and deterministic FFmpeg conversion."""

import hashlib
import ipaddress
import json
import subprocess
from pathlib import Path

import httpx
from pydantic import BaseModel, HttpUrl

MAX_MEDIA_BYTES = 50 * 1024 * 1024
MIN_DURATION_SECONDS = 0.1
MAX_DURATION_SECONDS = 60.0
VIDEO_FILTER = (
    'scale=1280:720:force_original_aspect_ratio=decrease,'
    'pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p'
)
AUDIO_FILTER = 'loudnorm=I=-16:TP=-1.5:LRA=11'


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
    info = MediaInfo.model_validate_json(process.stdout)
    info.get_stream('video')
    info.get_stream('audio')
    if not MIN_DURATION_SECONDS <= info.format.duration <= MAX_DURATION_SECONDS:
        raise ValueError('Clip duration must be between 0.1 and 60 seconds')
    return info


def verify_normalized(path: Path) -> None:
    """Check the codec, resolution, and frame rate of the final clip."""
    info = probe_media(path)
    video = info.get_stream('video')
    audio = info.get_stream('audio')
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


def download_media(url: HttpUrl, destination: Path) -> None:
    """Fetch one explicit HTTPS link without following redirects or HTML."""
    if url.scheme != 'https' or url.host == 'localhost':
        raise ValueError('Direct media URL must be publicly hosted HTTPS')
    try:
        ipaddress.ip_address(url.host or '')
    except ValueError:
        pass
    else:
        raise ValueError('Direct media URL cannot contain an IP address')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.download')
    try:
        with httpx.Client(follow_redirects=False, timeout=30) as client:
            with client.stream('GET', str(url)) as response:
                response.raise_for_status()
                if response.is_redirect:
                    raise ValueError('Download redirects are not followed')
                total = 0
                with temporary.open('wb') as output:
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_MEDIA_BYTES:
                            raise ValueError('Download exceeds 50 MB')
                        output.write(chunk)
        if not temporary.stat().st_size:
            raise ValueError('Downloaded media is empty')
        check_source(temporary, None)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def normalize_media(source: Path, destination: Path) -> None:
    """Convert a short reaction into predictable H.264/AAC MP4."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.partial.mp4')
    command = (
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
        '-i', str(source), '-map', '0:v:0', '-map', '0:a:0',
        '-vf', VIDEO_FILTER, '-af', AUDIO_FILTER,
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '48000', '-ac', '2',
        '-movflags', '+faststart', str(temporary),
    )
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        verify_normalized(temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
