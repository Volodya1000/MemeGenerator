"""Typed representation of the JSON produced by FFprobe."""

from pydantic import BaseModel


class MediaStream(BaseModel):
    """Video or audio stream metadata returned by FFprobe."""

    codec_type: str
    codec_name: str | None = None
    width: int | None = None
    height: int | None = None
    avg_frame_rate: str | None = None


class MediaFormat(BaseModel):
    """Container properties returned by FFprobe."""

    duration: float


class MediaInfo(BaseModel):
    """Parsed streams and format of one media file."""

    streams: list[MediaStream]
    format: MediaFormat

    def get_stream(self, stream_type: str) -> MediaStream:
        """Get a required stream or reject a video without it."""
        for stream in self.streams:
            if stream.codec_type == stream_type:
                return stream
        raise ValueError(f'Media must contain a {stream_type} stream')
