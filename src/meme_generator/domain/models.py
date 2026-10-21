"""Backward-compatible domain imports; use specific modules in new code."""

from meme_generator.domain.generated_video import GeneratedVideo
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene

__all__ = ('GeneratedVideo', 'Meme', 'Scenario', 'Scene')
