"""Regression tests for encoder timestamp drift in rendered reactions."""

from math import isclose

import pytest

from meme_generator.infrastructure.media.frame_search import find_frame_match

DISTANCE_LIMIT = 30.0
MATCHED_START = 17.0
EXPECTED_START = 19.0
SOURCE_DURATION = 2.0
OUTPUT_DURATION = 25.0
OUTSIDE_OUTPUT = 50.0
SHORT_OUTPUT = 10.0
MATCH_TOLERANCE = 0.01
MATCH_DISTANCE = 4.0
NO_MATCH_DISTANCE = 100.0


def shifted_frame(position: float, sample: float) -> float:
    """Represent footage shifted back after several concatenated clips."""
    aligned: bool = isclose(position, MATCHED_START, abs_tol=MATCH_TOLERANCE)
    if aligned and sample > 0:
        return MATCH_DISTANCE
    return NO_MATCH_DISTANCE


def absent_frame(position: float, sample: float) -> float:
    """Never match if genuine source footage is missing."""
    return NO_MATCH_DISTANCE


def test_recovers_from_accumulated_encoder_drift() -> None:
    """A valid later scene can match despite a small timestamp shift."""
    match = find_frame_match(
        expected_start=EXPECTED_START,
        source_duration=SOURCE_DURATION,
        output_duration=OUTPUT_DURATION,
        compare=shifted_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is not None
    assert match.position == pytest.approx(MATCHED_START)


def test_does_not_accept_unrelated_video() -> None:
    """A genuinely absent reaction still fails the authenticity check."""
    match = find_frame_match(
        expected_start=EXPECTED_START,
        source_duration=SOURCE_DURATION,
        output_duration=OUTPUT_DURATION,
        compare=absent_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is None


def test_keeps_samples_inside_output() -> None:
    """Never request output frames past the end of the MP4."""
    match = find_frame_match(
        expected_start=OUTSIDE_OUTPUT,
        source_duration=SOURCE_DURATION,
        output_duration=SHORT_OUTPUT,
        compare=shifted_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is None
