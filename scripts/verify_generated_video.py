"""Verify arbitrary LLM-selected reactions against the actual source clips."""

import logging
from pathlib import Path

from verify_real_review_frames import (
    MAX_PIXEL_DIFFERENCE,
    frame_distance,
)

from meme_generator.domain.scenario import Scenario
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import InMemoryMemeRepository

OUTPUT = Path('output/gemini-result.mp4')
CATALOG = Path('assets/catalog.json')
LOGGER = logging.getLogger(__name__)


def verify_source_clip(source: Path, start: float) -> None:
    """Reject movie segments unrelated to their selected real reaction."""
    distance = frame_distance(OUTPUT, source, start)
    if distance > MAX_PIXEL_DIFFERENCE:
        raise ValueError('Generated video contains unexpected media')
    LOGGER.info('SOURCE_MATCH distance=%.2f', distance)


def verify_generated_video() -> None:
    """Require real, source-matching footage in every planned reaction."""
    scenario = Scenario.model_validate_json(
        OUTPUT.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    catalog = InMemoryMemeRepository.from_json(CATALOG)
    if not OUTPUT.with_suffix('.attribution.json').is_file():
        raise FileNotFoundError('Attribution manifest is missing')
    position: float = 0
    for scene in scenario.scenes:
        source = catalog.get(scene.meme_id).video_path
        position += GenerationSettings().context_duration_seconds
        verify_source_clip(source, position)
        LOGGER.info('SCENE_VERIFIED %s', scene.order)
        position += probe_clip(source).duration_seconds
    if not probe_clip(OUTPUT).has_audio:
        raise ValueError('Generated movie has no audio')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    verify_generated_video()
