"""Reviewed three-reaction scenario for real-media visual acceptance."""

from meme_generator.application.scenario_validation import validate_plan
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene

REAL_STORY: tuple[tuple[str, str], ...] = (
    (
        'tinkov_somnitelno_no_okey',
        'Когда проверки проходят, но ролик никто не открывал',
    ),
    (
        'tinkov_kruto',
        'Когда GitHub собрал мемы без локального запуска',
    ),
    (
        'tinkov_skolko_mozhno',
        'Когда третий раз прислали видео без настоящих мемов',
    ),
)


class RealReviewPlanner:
    """Select known real source clips in a predefined readable story."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Build a real scenario without relying on LLM or invented IDs."""
        if scene_count != len(REAL_STORY):
            raise ValueError('All curated review scenes are required')
        scenario = Scenario(
            theme=theme,
            scenes=[
                Scene(
                    order=position,
                    description=caption,
                    image_query=caption,
                    meme_id=identifier,
                )
                for position, (identifier, caption) in enumerate(
                    REAL_STORY, start=1
                )
            ],
        )
        validate_plan(scenario, memes, scene_count)
        return scenario
