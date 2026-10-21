"""Check generation orchestration and provenance without real API calls."""

import json
from pathlib import Path

from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.planning import DemoPlanner
from meme_generator.domain.models import Meme, Scenario
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.images import LocalImageProvider


class FakeRenderer:
    """Renderer double for checking application plumbing."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeCatalog,
        images: list,
        output_path: Path,
    ) -> Path:
        """Create a marker output without invoking FFmpeg."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b'video stub')
        return output_path


def test_pipeline_provenance(tmp_path: Path) -> None:
    """Generation writes the plan, image licenses, and video together."""
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
