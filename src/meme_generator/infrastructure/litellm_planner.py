"""LiteLLM adapter for provider-neutral scene planning."""

import json
from collections.abc import Callable

from litellm import completion
from litellm.types.utils import ModelResponse

from meme_generator.application.scenario_validation import validate_plan
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario

LLM_TIMEOUT_SECONDS = 90

PLANNER_SYSTEM = (
    'You plan a short humorous reaction video. Return only JSON with keys '
    'theme and scenes. Each scene has order (1-based), description, '
    'image_query, meme_id. Choose meme_id ONLY from available_memes. '
    'Each image_query must be a concrete visual search query. '
    'Select reactions whose tone matches the illustrated situation. '
    'Keep situations connected and avoid unnecessary repetition.'
)


class LiteLLMPlanner:
    """Use a named LiteLLM model or any OpenAI-compatible base URL."""

    def __init__(
        self,
        model: str,
        api_base: str | None = None,
        api_key: str | None = None,
        generate_text: Callable[[str], str] | None = None,
    ) -> None:
        """Inject the completion boundary for deterministic tests."""
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._generate_text = generate_text or self._complete

    def _complete(self, user_content: str) -> str:
        """Normalize the external SDK response into plain JSON text."""
        response: object = completion(
            model=self._model,
            api_base=self._api_base,
            api_key=self._api_key,
            messages=[
                {'role': 'system', 'content': PLANNER_SYSTEM},
                {'role': 'user', 'content': user_content},
            ],
            response_format={'type': 'json_object'},
            temperature=0.6,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if not isinstance(response, ModelResponse) or not response.choices:
            raise ValueError('LLM returned an invalid completion response')
        content: object = response.choices[0].message.content
        if not isinstance(content, str):
            raise ValueError('LLM returned no textual scenario')
        return content

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Validate exact scene count and reaction membership."""
        request = json.dumps(
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
        raw = self._generate_text(request)
        scenario = Scenario.model_validate_json(raw)
        validate_plan(scenario, memes, scene_count)
        return scenario.model_copy(update={'theme': theme})
