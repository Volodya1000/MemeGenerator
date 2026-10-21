"""Black-box application behavior without invoking external services."""

import json
from pathlib import Path

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.in_memory_meme_repository import (
    InMemoryMemeRepository,
)
from tests.fakes.video_renderer import FakeRenderer


def test_pipeline_provenance(tmp_path: Path) -> None:
    """A valid request produces a video and traceable input metadata."""
    originals = tmp_path / 'images'
    originals.mkdir()
    (originals / '1.png').write_bytes(b'image')
    output_path = tmp_path / 'output' / 'result.mp4'
    video = GenerationPipeline(
        catalog=InMemoryMemeRepository(
            [
                Meme(
                    meme_id='reaction',
                    phrase='Surprised',
                    video_path=tmp_path / 'reaction.mp4',
                ),
            ]
        ),
        planner=DemoPlanner(),
        image_provider=LocalImageProvider(originals),
        renderer=FakeRenderer(),
    ).generate('Life in software', 1, output_path)
    scenario = json.loads(
        output_path.with_suffix('.scenario.json').read_text()
    )
    provenance = json.loads(
        output_path.with_suffix('.attribution.json').read_text(),
    )
    assert video.scene_count == 1
    assert scenario['scenes'][0]['meme_id'] == 'reaction'
    assert provenance[0]['license'] == 'User-provided'
    assert output_path.read_bytes() == b'video stub'
