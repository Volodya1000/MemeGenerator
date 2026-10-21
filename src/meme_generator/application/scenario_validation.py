"""Business rules for validating an externally planned scenario."""

from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario


def validate_plan(
    scenario: Scenario,
    memes: list[Meme],
    scene_count: int,
) -> None:
    """Reject made-up clips and the wrong number of scenes."""
    if len(scenario.scenes) != scene_count:
        raise ValueError('LLM returned the wrong number of scenes')
    known = {meme.meme_id for meme in memes}
    for scene in scenario.scenes:
        if scene.meme_id not in known:
            raise ValueError('LLM selected an unknown meme identifier')
