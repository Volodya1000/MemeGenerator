"""LiteLLM planning with typed requests and transient error retries."""

from collections.abc import Callable

from litellm import completion
from litellm.exceptions import (
    APIConnectionError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)
from litellm.types.utils import ModelResponse
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from meme_generator.application.protocols.scenario_planner import (
    ScenarioPlannerProtocol,
)
from meme_generator.application.scenario_validation import validate_plan
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.infrastructure.llm.request import (
    AvailableMeme,
    PlannerRequest,
)
from meme_generator.infrastructure.prompts.scenario import (
    PLANNER_SYSTEM_PROMPT,
)

LLM_TIMEOUT_SECONDS = 90
PLANNER_TEMPERATURE = 0.6
RETRY_MAX_WAIT_SECONDS = 8

TRANSIENT_ERRORS = (
    TimeoutError,
    ConnectionError,
    APIConnectionError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)


class LiteLLMPlanner(ScenarioPlannerProtocol):
    """Plan scenes without binding callers to any one LLM provider."""

    def __init__(
        self,
        model: str,
        api_base: str | None = None,
        api_key: str | None = None,
        generate_text: Callable[[str], str] | None = None,
        retry_attempts: int = 3,
    ) -> None:
        """Allow deterministic fakes without mocking every SDK method."""
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._generate_text = generate_text or self._complete
        self._retry_attempts = retry_attempts

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Retry transient failures, then validate strict domain invariants."""
        request = PlannerRequest(
            topic=theme,
            scene_count=scene_count,
            available_memes=[
                AvailableMeme(meme_id=meme.meme_id, phrase=meme.phrase)
                for meme in memes
            ],
        )
        retrying = Retrying(
            retry=retry_if_exception_type(TRANSIENT_ERRORS),
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(max=RETRY_MAX_WAIT_SECONDS),
            reraise=True,
        )
        raw: str = retrying(
            self._generate_text,
            request.model_dump_json(),
        )
        scenario = Scenario.model_validate_json(raw)
        validate_plan(scenario, memes, scene_count)
        return scenario.model_copy(update={'theme': theme})

    def _complete(self, user_prompt: str) -> str:
        """Normalize LiteLLM SDK objects into textual JSON responses."""
        response: object = completion(
            model=self._model,
            api_base=self._api_base,
            api_key=self._api_key,
            messages=[
                {'role': 'system', 'content': PLANNER_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=PLANNER_TEMPERATURE,
            timeout=LLM_TIMEOUT_SECONDS,
            num_retries=0,
        )
        if not isinstance(response, ModelResponse) or not response.choices:
            raise ValueError('LLM returned an invalid completion response')
        response_text: object = response.choices[0].message.content
        if not isinstance(response_text, str):
            raise TypeError('LLM returned no textual scenario')
        return response_text
