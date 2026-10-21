"""Contracts of generated scenarios."""

import pytest
from pydantic import ValidationError

from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene


def test_ordered_scenario_is_accepted() -> None:
    """A valid scenario keeps all scenes in the supplied order."""
    scene = Scene(
        order=1,
        description='A developer sees an error',
        image_query='developer error screen',
        meme_id='reaction-1',
    )
    scenario = Scenario(theme='Developer life', scenes=[scene])
    assert scenario.scenes[0].meme_id == 'reaction-1'


def test_scene_gap_is_rejected() -> None:
    """A scenario cannot silently omit scene numbers."""
    scene = Scene(
        order=2,
        description='Broken build',
        image_query='broken code',
        meme_id='reaction-1',
    )
    with pytest.raises(ValidationError):
        Scenario(theme='Developer life', scenes=[scene])
