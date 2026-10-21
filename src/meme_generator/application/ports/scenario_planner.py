"""Scenario generation port independent of LLM provider."""

from typing import Protocol

from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario


class ScenarioPlanner(Protocol):
    """Produce a validated ordered plan using an approved catalog."""

    def plan(
        self,
        theme: str,
        memes: list[Meme],
        scene_count: int,
    ) -> Scenario:
        """Produce the narrative for the requested scene count."""
        ...
