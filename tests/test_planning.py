"""LLMs cannot reference clips missing from the curated catalog."""

import json
from pathlib import Path

import httpx
import pytest

from meme_generator.application.planning import DemoPlanner, OpenAIPlanner
from meme_generator.domain.models import Meme

REACTION_ID = 'known'
TEST_TOPIC = 'Developer life'
HTTP_OK = 200


def sample_memes() -> list[Meme]:
    """Provide a minimal approved reaction catalog."""
    return [
        Meme(
            meme_id=REACTION_ID,
            phrase='Surprised reaction',
            video_path=Path('clip.mp4'),
        ),
    ]


def response_payload(meme_id: str) -> dict:
    """Build a minimal OpenAI-compatible chat response."""
    raw = {
        'theme': 'Model theme',
        'scenes': [
            {
                'order': 1,
                'description': 'A developer sees failed tests',
                'image_query': 'failed tests screen',
                'meme_id': meme_id,
            }
        ],
    }
    return {'choices': [{'message': {'content': json.dumps(raw)}}]}


def test_demo_is_deterministic() -> None:
    """Offline mode preserves all ordered scenes."""
    scenario = DemoPlanner().plan(TEST_TOPIC, sample_memes(), 2)
    assert [scene.order for scene in scenario.scenes] == [1, 2]
    assert {scene.meme_id for scene in scenario.scenes} == {REACTION_ID}


def test_planner_accepts_known_reaction() -> None:
    """A known identifier is a valid, grounded model response."""
    reply = response_payload(REACTION_ID)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(HTTP_OK, json=reply),
    )
    with httpx.Client(transport=transport) as client:
        scenario = OpenAIPlanner(
            'https://example.test/v1',
            'model',
            'key',
            client,
        ).plan(TEST_TOPIC, sample_memes(), 1)
    assert scenario.theme == TEST_TOPIC
    assert scenario.scenes[0].meme_id == REACTION_ID


def test_planner_rejects_hallucinated_reaction() -> None:
    """LLM output cannot hallucinate a non-existent source clip."""
    reply = response_payload('imaginary')
    transport = httpx.MockTransport(
        lambda request: httpx.Response(HTTP_OK, json=reply),
    )
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(ValueError, match='unknown'),
    ):
        OpenAIPlanner(
            'https://example.test/v1',
            'model',
            'key',
            client,
        ).plan(TEST_TOPIC, sample_memes(), 1)
