"""Deterministic, offline scenario generation."""

from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene


class DemoPlanner:
    """Repeat supplied reactions to test the video pipeline offline."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Create reproducible scene descriptions and reaction IDs."""
        if not memes:
            raise ValueError('Cannot plan a scenario with an empty catalog')
        if scene_count < 1:
            raise ValueError('At least one scene is required')
        scenes = [
            Scene(
                order=index,
                description=f'{theme}: situation {index}',
                image_query=f'{theme} situation {index}',
                meme_id=memes[(index - 1) % len(memes)].meme_id,
            )
            for index in range(1, scene_count + 1)
        ]
        return Scenario(theme=theme, scenes=scenes)
