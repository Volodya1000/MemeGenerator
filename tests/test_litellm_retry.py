"""State-based retry policy tests without external LLM dependencies."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.litellm_planner import LiteLLMPlanner

MODEL_NAME = 'openai/test'


class RecoveringCompletion:
    """Fake provider that recovers after an initial connection error."""

    def __init__(self) -> None:
        """Start with no outbound completion attempts."""
        self.attempts: int = 0

    def __call__(self, request: str) -> str:
        """Return a valid scenario only after a transient failure."""
        self.attempts += 1
        if self.attempts == 1:
            raise ConnectionError('transient model outage')
        return Scenario(
            theme='Draft',
            scenes=[
                Scene(
                    order=1,
                    description='Working on a program',
                    image_query='computer screen',
                    meme_id='approved',
                )
            ],
        ).model_dump_json()


class InvalidCompletion:
    """Fake provider that always returns invalid structured output."""

    def __init__(self) -> None:
        """Track attempts that should not be repeated."""
        self.attempts: int = 0

    def __call__(self, request: str) -> str:
        """Return a malformed response for permanent-failure testing."""
        self.attempts += 1
        return 'not json'


def test_transient_error_is_retried() -> None:
    """The model retry policy handles a temporary connection outage."""
    provider = RecoveringCompletion()
    planner = LiteLLMPlanner(
        MODEL_NAME,
        generate_text=provider,
        retry_attempts=2,
    )
    memes = [
        Meme(
            meme_id='approved',
            phrase='Agreed',
            video_path=Path('clip.mp4'),
        )
    ]
    scenario = planner.plan('Programming', memes, 1)
    assert scenario.scenes[0].meme_id == 'approved'
    assert provider.attempts == 2


def test_bad_json_does_not_retry() -> None:
    """Validation failures are not mistaken for temporary transport errors."""
    provider = InvalidCompletion()
    planner = LiteLLMPlanner(
        MODEL_NAME,
        generate_text=provider,
        retry_attempts=3,
    )
    memes = [
        Meme(
            meme_id='approved',
            phrase='Agreed',
            video_path=Path('clip.mp4'),
        )
    ]
    with pytest.raises(ValidationError):
        planner.plan('Programming', memes, 1)
    assert provider.attempts == 1
