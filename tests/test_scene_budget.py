"""Scene counts follow real clip lengths and strict duration policies."""

import pytest

from meme_generator.application.scene_budget import (
    MAX_TARGET_SECONDS,
    MAX_VIDEO_SCENES,
    SceneBudgetError,
    estimate_scene_count,
)

CONTEXT_SECONDS = 2.0
SHORT_REACTION_SECONDS = 2.0
LONG_REACTION_SECONDS = 8.0
MINIMAL_REACTION_SECONDS = 0.5
TARGET_SECONDS = 30
SHORT_TARGET_SECONDS = 20
EXPECTED_SCENES = 3


def test_target_duration_uses_actual_clip_lengths() -> None:
    """Longer reactions naturally produce fewer individual scenes."""
    fast = estimate_scene_count(
        TARGET_SECONDS, [SHORT_REACTION_SECONDS], CONTEXT_SECONDS
    )
    slow = estimate_scene_count(
        TARGET_SECONDS, [LONG_REACTION_SECONDS], CONTEXT_SECONDS
    )
    assert fast > slow


def test_requested_duration_is_an_estimate() -> None:
    """A measured average, not a hand-picked meme, drives the estimate."""
    assert estimate_scene_count(
        SHORT_TARGET_SECONDS, [3.0, 5.0], CONTEXT_SECONDS
    ) == EXPECTED_SCENES


def test_extreme_target_respects_scene_limit() -> None:
    """The output remains bounded even if clips are exceptionally short."""
    assert estimate_scene_count(
        MAX_TARGET_SECONDS, [MINIMAL_REACTION_SECONDS], CONTEXT_SECONDS
    ) == MAX_VIDEO_SCENES


@pytest.mark.parametrize(
    ('target', 'clips', 'context'),
    [
        (0, [SHORT_REACTION_SECONDS], CONTEXT_SECONDS),
        (MAX_TARGET_SECONDS + 1, [SHORT_REACTION_SECONDS], CONTEXT_SECONDS),
        (SHORT_TARGET_SECONDS, [], CONTEXT_SECONDS),
        (SHORT_TARGET_SECONDS, [0], CONTEXT_SECONDS),
        (SHORT_TARGET_SECONDS, [float('nan')], CONTEXT_SECONDS),
        (SHORT_TARGET_SECONDS, [SHORT_REACTION_SECONDS], 0),
    ],
)
def test_invalid_duration_inputs_are_rejected(
    target: int,
    clips: list[float],
    context: float,
) -> None:
    """Invalid metadata does not create an apparently valid scene count."""
    with pytest.raises(SceneBudgetError):
        estimate_scene_count(target, clips, context)
