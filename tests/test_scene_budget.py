"""Scene count policy uses real clip lengths, not invented constants."""

import pytest

from meme_generator.application.scene_budget import estimate_scene_count


def test_target_duration_uses_actual_clip_lengths() -> None:
    """The same target gives fewer scenes for longer reaction clips."""
    fast = estimate_scene_count(30, [2.0, 2.0, 2.0], 2.0)
    slow = estimate_scene_count(30, [8.0, 8.0, 8.0], 2.0)
    assert fast > slow


def test_requested_duration_is_an_estimate() -> None:
    """The context and measured mean determine the scene count."""
    assert estimate_scene_count(20, [3.0, 5.0], 2.0) == 3


def test_extreme_target_respects_scene_limit() -> None:
    """Never generate more than the supported maximum number of scenes."""
    assert estimate_scene_count(180, [0.5, 0.5], 2.0) == 10


@pytest.mark.parametrize(
    ('target', 'clips', 'context'),
    [
        (0, [2.0], 2.0),
        (181, [2.0], 2.0),
        (20, [], 2.0),
        (20, [0.0], 2.0),
        (20, [float('nan')], 2.0),
        (20, [2.0], 0.0),
    ],
)
def test_invalid_duration_inputs_are_rejected(
    target: int,
    clips: list[float],
    context: float,
) -> None:
    """Broken metadata cannot produce a plausible but incorrect estimate."""
    with pytest.raises(ValueError):
        estimate_scene_count(target, clips, context)
