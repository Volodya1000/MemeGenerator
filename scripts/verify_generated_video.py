"""Verify generated reaction scenes against genuine source video frames."""

import logging
from functools import partial
from pathlib import Path

from verify_real_review_frames import (
    MAX_PIXEL_DIFFERENCE,
    frame_distance,
)

from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.clip_info import ClipInfo
from meme_generator.domain.scenario import Scenario
from meme_generator.domain.scene import Scene
from meme_generator.infrastructure.media.frame_search import find_frame_match
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import InMemoryMemeRepository

OUTPUT = Path('output/gemini-result.mp4')
CATALOG = Path('assets/catalog.json')
LOGGER = logging.getLogger(__name__)


def verify_source_clip(
    source: Path,
    expected_start: float,
    source_duration: float,
    output_duration: float,
) -> None:
    """Check the genuine footage, allowing limited encoder timestamp drift."""
    match = find_frame_match(
        expected_start=expected_start,
        source_duration=source_duration,
        output_duration=output_duration,
        compare=partial(frame_distance, OUTPUT, source),
        max_difference=MAX_PIXEL_DIFFERENCE,
    )
    if match is None:
        raise ValueError(
            f'Source footage mismatch: {source.name}, '
            f'expected time {expected_start:.2f}s'
        )
    LOGGER.info(
        'SOURCE_MATCH source=%s expected=%.2f actual=%.2f distance=%.2f',
        source.name,
        expected_start,
        match.position,
        match.distance,
    )


def _verify_scene(
    scene: Scene,
    catalog: InMemoryMemeRepository,
    position: float,
    output_duration: float,
) -> float:
    """Check one genuine reaction and calculate the next nominal offset."""
    source: Path = catalog.get(scene.meme_id).video_path
    source_clip: ClipInfo = probe_clip(source)
    start: float = position + GenerationSettings().context_duration_seconds
    verify_source_clip(
        source,
        start,
        source_clip.duration_seconds,
        output_duration,
    )
    LOGGER.info('SCENE_VERIFIED %s', scene.order)
    return start + source_clip.duration_seconds


def verify_generated_video() -> None:
    """Require audio and authentic reactions for all generated scenes."""
    scenario: Scenario = Scenario.model_validate_json(
        OUTPUT.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    catalog: InMemoryMemeRepository = InMemoryMemeRepository.from_json(CATALOG)
    output_clip: ClipInfo = probe_clip(OUTPUT)
    if not OUTPUT.with_suffix('.attribution.json').is_file():
        raise FileNotFoundError('Attribution manifest is missing')
    position: float = 0
    for scene in scenario.scenes:
        position = _verify_scene(
            scene, catalog, position, output_clip.duration_seconds
        )
    if not output_clip.has_audio:
        raise ValueError('Generated movie has no audio')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    verify_generated_video()
