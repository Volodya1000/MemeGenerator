"""End-to-end orchestration with real SQL and a fake video encoder."""

import json
from pathlib import Path

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)
from meme_generator.infrastructure.images import LocalImageProvider
from tests.fakes.video_renderer import FakeRenderer


def test_sql_backend_generates_video_manifests(
    sql_repository: SqlAlchemyMemeRepository,
    tmp_path: Path,
) -> None:
    """The use case behaves identically with an actual SQL repository."""
    image_dir = tmp_path / 'images'
    image_dir.mkdir()
    (image_dir / '1.png').write_bytes(b'context')
    sql_repository.replace_all(
        [
            Meme(
                meme_id='approved',
                phrase='Wow',
                video_path=tmp_path / 'reaction.mp4',
            ),
        ],
    )
    output_path = tmp_path / 'rendered' / 'result.mp4'
    generated = GenerationPipeline(
        catalog=sql_repository,
        planner=DemoPlanner(),
        image_provider=LocalImageProvider(image_dir),
        renderer=FakeRenderer(),
    ).generate('Programming', 1, output_path)
    scenario = json.loads(
        output_path.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    assert generated.output_path == output_path
    assert output_path.read_bytes() == b'video stub'
    assert scenario['scenes'][0]['meme_id'] == 'approved'
