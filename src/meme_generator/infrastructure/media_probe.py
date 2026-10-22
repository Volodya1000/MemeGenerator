"""Use typed FFprobe metadata to verify media before rendering."""

from pathlib import Path

from meme_generator.domain.clip_info import ClipInfo
from meme_generator.infrastructure.media.ffprobe import inspect_media
from meme_generator.infrastructure.media.metadata import MediaInfo


def probe_clip(path: Path) -> ClipInfo:
    """Reject unreadable clips and media without video streams."""
    media: MediaInfo = inspect_media(path)
    media.get_stream('video')
    has_audio: bool = any(
        stream.codec_type == 'audio' for stream in media.streams
    )
    return ClipInfo(
        duration_seconds=media.format.duration,
        has_audio=has_audio,
    )
