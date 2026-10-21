"""Black-box application behavior without invoking external services."""

import json
from pathlib import Path

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.meme import Meme
from meme_generator.domain.scenario import Scenario
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.images import LocalImageProvider


class FakeRenderer:
    """File-producing external boundary for fast orchestration tests."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeRepository,
        images: list[ImageAsset],
        output_path: Path,
    ) -> Path:
        """Write a recognizable artifact without using FFmpeg."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b'video stub')
        return output_path


def test_pipeline_provenance(tmp_path: Path) -> None:
    """A valid request produces a video and traceable input metadata."""
    originals = tmp_path / 'images'
    originals.mkdir()
    (originals / '1.png').write_bytes(b'image')
    output_path = tmp_path / 'output' / 'result.mp4'
    video = GenerationPipeline(
        catalog=MemeCatalog(
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
