"""Deterministic meaningful script for remote media acceptance."""

from meme_generator.application.scenario_validation import validate_plan
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene

STORY: tuple[tuple[str, str, str], ...] = (
    (
        'doubtful',
        'Сомнительно, но окей',
        'Когда проверки зелёные, но видео ещё никто не видел',
    ),
    (
        'great',
        'Круто, да это ж круто!',
        'Когда GitHub собрал настоящий MP4 вообще без твоего ноутбука',
    ),
    (
        'enough',
        'Сколько можно!',
        'Когда в маленьком PR снова обнаружилось 300 замечаний',
    ),
)


class PreviewPlanner:
    """Select three known reactions without pretending to involve an LLM."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Build and validate a specific reviewable story."""
        if scene_count != len(STORY):
            raise ValueError('Preview must include every scripted reaction')
        scenario = Scenario(
            theme=theme,
            scenes=[
                Scene(
                    order=index,
                    description=context,
                    image_query=context,
                    meme_id=identifier,
                )
                for index, (identifier, _, context) in enumerate(
                    STORY, start=1
                )
            ],
        )
        validate_plan(scenario, memes, scene_count)
        return scenario
