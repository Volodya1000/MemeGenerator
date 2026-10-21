"""Provider-independent black-box tests for externally planned scenes."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.litellm_planner import LiteLLMPlanner

REACTION_ID = 'known'
TEST_TOPIC = 'Developer life'
MODEL_NAME = 'openai/test'


def sample_memes() -> list[Meme]:
    """One approved video reaction with an exact phrase."""
    return [
        Meme(
            meme_id=REACTION_ID,
            phrase='Surprised reaction',
            video_path=Path('clip.mp4'),
        ),
    ]


def response_content(meme_id: str, count: int = 1) -> str:
    """Return a complete synthetic LLM response, without HTTP."""
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


def test_planner_accepts_existing_reaction() -> None:
    """The result uses an approved clip and retains the user's theme."""
    planner = LiteLLMPlanner(
        MODEL_NAME,
        generate_text=lambda _: response_content(REACTION_ID),
    )
    scenario = planner.plan(TEST_TOPIC, sample_memes(), 1)
    assert scenario.theme == TEST_TOPIC
    assert scenario.scenes[0].meme_id == REACTION_ID


def test_planner_rejects_hallucinated_reaction() -> None:
    """A fabricated meme ID never reaches the renderer."""
    planner = LiteLLMPlanner(
        MODEL_NAME,
        generate_text=lambda _: response_content('imaginary'),
    )
    with pytest.raises(ValueError, match='unknown'):
        planner.plan(TEST_TOPIC, sample_memes(), 1)


def test_planner_rejects_wrong_scene_count() -> None:
    """The model cannot silently shorten a requested scenario."""
    planner = LiteLLMPlanner(
        MODEL_NAME,
        generate_text=lambda _: response_content(REACTION_ID, 2),
    )
    with pytest.raises(ValueError, match='wrong number'):
        planner.plan(TEST_TOPIC, sample_memes(), 1)


def test_model_response_must_be_valid_json() -> None:
    """Malformed output cannot be accepted as a partial scenario."""
    planner = LiteLLMPlanner(MODEL_NAME, generate_text=lambda _: 'not json')
    with pytest.raises(ValidationError):
        planner.plan(TEST_TOPIC, sample_memes(), 1)
