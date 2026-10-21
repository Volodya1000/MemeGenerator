"""Black-box scenario planning tests, independent of model providers."""

import json
from pathlib import Path

import pytest

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.litellm_planner import LiteLLMPlanner


def sample_memes() -> list[Meme]:
    """One legally supplied reaction available to the planner."""
    return [
        Meme(
            meme_id='known',
            phrase='Surprised reaction',
            video_path=Path('clip.mp4'),
        ),
    ]


def response_content(meme_id: str, count: int = 1) -> str:
    """Return a complete synthetic model response, not an HTTP mock."""
    scenes = [
        {
            'order': index,
            'description': 'A developer encounters errors',
            'image_query': 'errors on a monitor',
            'meme_id': meme_id,
        }
        for index in range(1, count + 1)
    ]
    return json.dumps({'theme': 'Draft', 'scenes': scenes})


def test_demo_is_deterministic() -> None:
    """Stable topics and catalog return stable, ordered scenes."""
    scenario = DemoPlanner().plan('Developer life', sample_memes(), 2)
    assert [scene.order for scene in scenario.scenes] == [1, 2]
    assert {scene.meme_id for scene in scenario.scenes} == {'known'}


def test_planner_accepts_existing_reaction() -> None:
    """Use an approved identifier and return the original user theme."""
    planner = LiteLLMPlanner('openai/test', generate_text=lambda _: response_content('known'))
    scenario = planner.plan('Developer life', sample_memes(), 1)
    assert scenario.theme == 'Developer life'
    assert scenario.scenes[0].meme_id == 'known'


def test_planner_rejects_hallucinated_reaction() -> None:
    """A fabricated reaction ID cannot reach the video renderer."""
    planner = LiteLLMPlanner('openai/test', generate_text=lambda _: response_content('imaginary'))
    with pytest.raises(ValueError, match='unknown'):
        planner.plan('Developer life', sample_memes(), 1)


def test_planner_rejects_wrong_scene_count() -> None:
    """The model cannot silently shorten the user's requested video."""
    planner = LiteLLMPlanner('openai/test', generate_text=lambda _: response_content('known', 2))
    with pytest.raises(ValueError, match='wrong number'):
        planner.plan('Developer life', sample_memes(), 1)


def test_demo_rejects_empty_memes() -> None:
    """Empty input has an explicit domain error instead of modulo zero."""
    with pytest.raises(ValueError, match='empty catalog'):
        DemoPlanner().plan('Developer life', [], 2)


def test_model_response_must_be_valid_json() -> None:
    """Invalid model output must not become a partly valid scenario."""
    planner = LiteLLMPlanner('openai/test', generate_text=lambda _: 'not json')
    with pytest.raises(ValueError):
        planner.plan('Developer life', sample_memes(), 1)
