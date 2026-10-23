"""Regression tests for cumulative timestamp drift in rendered reaction clips."""

from meme_generator.infrastructure.media.frame_search import find_frame_match

DISTANCE_LIMIT = 30.0


def shifted_frame(position: float, sample: float) -> float:
    """Represent footage shifted back two seconds after several clips."""
    if abs(position - 17.0) < 0.01 and sample > 0:
        return 4.0
    return 100.0


def absent_frame(position: float, sample: float) -> float:
    """Never match if source footage is absent from the video."""
    return 100.0


def test_recovers_from_accumulated_encoder_drift() -> None:
    """An otherwise correct sixth scene must survive slight timestamp drift."""
    match = find_frame_match(
        expected_start=19.0,
        source_duration=2.0,
        output_duration=25.0,
        compare=shifted_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is not None
    assert match.position == 17.0


def test_does_not_accept_unrelated_video() -> None:
    """A failed source-image check must not be silently skipped."""
    match = find_frame_match(
        expected_start=19.0,
        source_duration=2.0,
        output_duration=25.0,
        compare=absent_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is None


def test_keeps_samples_inside_output() -> None:
    """Never decode a future frame beyond the rendered MP4 duration."""
    match = find_frame_match(
        expected_start=50.0,
        source_duration=1.0,
        output_duration=10.0,
        compare=shifted_frame,
        max_difference=DISTANCE_LIMIT,
    )
    assert match is None
