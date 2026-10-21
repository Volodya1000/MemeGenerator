"""Generate grounded, validated scene plans from a fixed clip catalog."""

import json
from typing import Protocol

import httpx

from meme_generator.domain.models import Meme, Scenario, Scene

LLM_TIMEOUT_SECONDS = 90

PLANNER_SYSTEM = (
    'You plan a short humorous reaction video. Return only JSON with keys '
    'theme and scenes. Each scene has order (1-based), description, '
    'image_query, meme_id. Choose meme_id ONLY from available_memes. '
    'Each image_query must be a concrete visual search query. '
    'Select reactions whose tone matches the illustrated situation. '
    'Keep the situations connected and avoid unnecessary repetition.'
)


class ScenarioPlanner(Protocol):
    """Port allowing online and deterministic offline planning."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Produce a validated narrative using the available reactions."""
        ...


def validate_reactions(scenario: Scenario, memes: list[Meme]) -> None:
    """Reject fabricated reactions and references to absent videos."""
    known = {meme.meme_id for meme in memes}
    for scene in scenario.scenes:
        if scene.meme_id not in known:
            raise ValueError('LLM selected an unknown meme identifier')


class OpenAIPlanner:
    """OpenAI-compatible chat planner, including local LLM endpoints."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        client: httpx.Client | None = None,
    ) -> None:
        """Store endpoint settings and an injectable HTTP transport."""
        self._url = f'{base_url.rstrip("/")}/chat/completions'
        self._model = model
        self._api_key = api_key
        self._client = client or httpx.Client(timeout=LLM_TIMEOUT_SECONDS)

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Ask the model for JSON and validate every returned clip ID."""
        request_content = json.dumps(
            {
                'topic': theme,
                'scene_count': scene_count,
                'available_memes': [
                    {'meme_id': meme.meme_id, 'phrase': meme.phrase}
                    for meme in memes
                ],
            },
            ensure_ascii=False,
        )
        response = self._client.post(
            self._url,
            headers={'Authorization': f'Bearer {self._api_key}'},
            json={
                'model': self._model,
                'response_format': {'type': 'json_object'},
                'temperature': 0.6,
                'messages': [
                    {'role': 'system', 'content': PLANNER_SYSTEM},
                    {'role': 'user', 'content': request_content},
                ],
            },
        )
        response.raise_for_status()
        raw = response.json()['choices'][0]['message']['content']
        scenario = Scenario.model_validate_json(raw)
        if len(scenario.scenes) != scene_count:
            raise ValueError('LLM returned the wrong number of scenes')
        validate_reactions(scenario, memes)
        return scenario.model_copy(update={'theme': theme})


class DemoPlanner:
    """Deterministic planner for offline video assembly and testing."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Create predictable scenes without network or inference."""
        scenes = [
            Scene(
                order=scene_order,
                description=f'{theme}: situation {scene_order}',
                image_query=f'{theme} situation {scene_order}',
                meme_id=memes[(scene_order - 1) % len(memes)].meme_id,
            )
            for scene_order in range(1, scene_count + 1)
        ]
        return Scenario(theme=theme, scenes=scenes)
