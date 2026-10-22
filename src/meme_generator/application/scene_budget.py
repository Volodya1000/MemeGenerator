"""Translate a requested video duration into a realistic scene count."""

import math
from collections.abc import Sequence

MAX_VIDEO_SCENES = 10
MIN_TARGET_SECONDS = 5
MAX_TARGET_SECONDS = 180


def _mean_clip_duration(durations: Sequence[float]) -> float:
    """Average measured lengths of playable source clips."""
    if not durations:
        raise ValueError('A nonempty video catalog is required')
    if any(not math.isfinite(value) or value <= 0 for value in durations):
        raise ValueError('Source clip durations must be finite and positive')
    return math.fsum(durations) / len(durations)


def estimate_scene_count(
    target_seconds: int,
    clip_durations_seconds: Sequence[float],
    context_seconds: float,
) -> int:
    """Estimate scene count from measured reactions and context duration."""
    if not MIN_TARGET_SECONDS <= target_seconds <= MAX_TARGET_SECONDS:
        raise ValueError('Requested duration is outside supported bounds')
    if not math.isfinite(context_seconds) or context_seconds <= 0:
        raise ValueError('Context display duration must be positive')
    return min(
        MAX_VIDEO_SCENES,
        max(
            1,
            round(
                target_seconds
                / (_mean_clip_duration(clip_durations_seconds) + context_seconds)
            ),
        ),
    )
