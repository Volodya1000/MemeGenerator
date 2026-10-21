"""Fast deterministic planning without model provider integration."""

from pathlib import Path

import pytest

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.domain.meme import Meme


def test_demo_is_deterministic() -> None:
    """Offline planning preserves contiguous scene order."""
    memes = [Meme(meme_id='known', phrase='Surprise', video_path=Path('clip.mp4'))]
    scenario = DemoPlanner().plan('Developer life', memes, 2)
    assert [scene.order for scene in scenario.scenes] == [1, 2]
    assert {scene.meme_id for scene in scenario.scenes} == {'known'}


def test_demo_rejects_empty_memes() -> None:
    """An empty catalog has an explicit business error."""
    with pytest.raises(ValueError, match='empty catalog'):
        DemoPlanner().plan('Developer life', [], 2)
