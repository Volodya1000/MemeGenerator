"""Locate an encoded reaction frame despite small concat timestamp drift."""

import subprocess
from collections.abc import Callable
from dataclasses import dataclass

FRAME_SAMPLE_SECONDS = 0.75
MIN_SAMPLE_SECONDS = 0.05
TIMESTAMP_OFFSETS: tuple[float, ...] = (
    0.0,
    -0.25,
    0.25,
    -0.5,
    0.5,
    -0.75,
    0.75,
    -1.0,
    1.0,
    -1.5,
    1.5,
    -2.0,
    2.0,
    -2.5,
    2.5,
    -3.0,
    3.0,
)


@dataclass(frozen=True, slots=True)
class MatchedFrame:
    """Source frame found in the rendered output at an actual timestamp."""

    position: float
    distance: float


def _sample_seconds(source_duration: float) -> float:
    """Avoid sampling beyond the end of a short source clip."""
    return min(
        FRAME_SAMPLE_SECONDS,
        max(MIN_SAMPLE_SECONDS, source_duration / 3),
    )


def find_frame_match(
    expected_start: float,
    source_duration: float,
    output_duration: float,
    compare: Callable[[float, float], float],
    max_difference: float,
) -> MatchedFrame | None:
    """Match genuine frames, trying bounded offsets around the estimate."""
    sample: float = _sample_seconds(source_duration)
    for offset in TIMESTAMP_OFFSETS:
        candidate: float = expected_start + offset
        if candidate < 0 or candidate + sample >= output_duration:
            continue
        try:
            distance: float = compare(candidate, sample)
        except (OSError, ValueError, subprocess.CalledProcessError):
            continue
        if distance <= max_difference:
            return MatchedFrame(position=candidate, distance=distance)
    return None
