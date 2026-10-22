"""Render a real, reviewable three-reaction video from pinned sources."""

import logging
from pathlib import Path

from real_review_story import REAL_STORY, RealReviewPlanner

from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.domain.scenario import Scenario
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import InMemoryMemeRepository

CATALOG = Path('assets/catalog.json')
OUTPUT = Path('output/real-reactions-review.mp4')
LOGGER = logging.getLogger(__name__)


def verify_generated_video(output: Path) -> None:
    """Check playback, scene sequence and published provenance."""
    media = probe_clip(output)
    if not media.has_audio or media.duration_seconds <= len(REAL_STORY) * 2:
        raise ValueError('Real review video lacks expected audio or scenes')
    if not all(
        path.is_file()
        for path in (
            output.with_suffix('.scenario.json'),
            output.with_suffix('.attribution.json'),
        )
    ):
        raise FileNotFoundError('Review video manifests were not published')
    scenario = Scenario.model_validate_json(
        output.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    if tuple(scene.meme_id for scene in scenario.scenes) != tuple(
        identifier for identifier, _ in REAL_STORY
    ):
        raise ValueError('Real review video has an incorrect clip sequence')
    LOGGER.info(
        'REAL_VIDEO_REVIEW_READY path=%s scenes=%s duration=%s',
        output,
        len(scenario.scenes),
        media.duration_seconds,
    )


def main() -> None:
    """Publish the actual source-backed MP4, never a synthetic substitute."""
    GenerationPipeline(
        catalog=InMemoryMemeRepository.from_json(CATALOG),
        planner=RealReviewPlanner(),
        image_provider=CaptionCardImageProvider(),
        renderer=FFmpegRenderer(),
    ).generate('Реакции разработчика', len(REAL_STORY), OUTPUT)
    verify_generated_video(OUTPUT)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
