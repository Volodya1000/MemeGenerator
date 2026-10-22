"""Check that rendered scenes include actual Commons photographs."""

import logging
import subprocess
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image

from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.attribution import (
    AttributionManifest,
    SceneAttribution,
)
from meme_generator.domain.scenario import Scenario
from meme_generator.infrastructure.media_probe import probe_clip
from meme_generator.persistence.in_memory import InMemoryMemeRepository

OUTPUT = Path('output/gemini-result.mp4')
CATALOG = Path('assets/catalog.json')
TEXT_CARD_LICENSE = 'Original generated typography'
PHOTO_DOMAINS = frozenset(('commons.wikimedia.org', 'upload.wikimedia.org'))
MIN_PHOTO_ENTROPY = 3.0
LOGGER = logging.getLogger(__name__)


def _frame_entropy(encoded: bytes) -> float:
    """Measure photographic variation outside the text-caption area."""
    with Image.open(BytesIO(encoded)) as decoded:
        grayscale = decoded.convert('L')
        frame_width, frame_height = grayscale.size
        scene_area = grayscale.crop(
            (
                frame_width // 10,
                frame_height // 10,
                frame_width * 9 // 10,
                frame_height // 2,
            )
        )
        return scene_area.entropy()


def _verify_photo_frame(position: float, order: int) -> None:
    """Reject flat text-only frames even when metadata claims a photograph."""
    command: list[str] = [
        'ffmpeg',
        '-hide_banner',
        '-loglevel',
        'error',
        '-ss',
        str(position),
        '-i',
        str(OUTPUT),
        '-frames:v',
        '1',
        '-f',
        'image2pipe',
        '-vcodec',
        'png',
        '-',
    ]
    encoded: subprocess.CompletedProcess[bytes] = subprocess.run(
        command,
        check=True,
        capture_output=True,
    )
    entropy = _frame_entropy(encoded.stdout)
    LOGGER.info('PHOTO_FRAME scene=%d entropy=%.2f', order, entropy)
    if entropy < MIN_PHOTO_ENTROPY:
        raise ValueError('Video contains a text card instead of a photo')


def _verify_attribution(
    scene_order: int,
    query: str,
    attribution: SceneAttribution | None,
) -> None:
    """Require provenance for the exact scene and an authentic Commons URL."""
    if attribution is None or attribution.license == TEXT_CARD_LICENSE:
        raise ValueError('Real Commons photograph missing for scene')
    origin = urlsplit(attribution.source_url)
    if origin.scheme != 'https' or origin.hostname not in PHOTO_DOMAINS:
        raise ValueError('Photo provenance must point to Wikimedia Commons')
    if attribution.query != query:
        raise ValueError('Photo attribution does not match the scene query')
    LOGGER.info(
        'PHOTO_PROVENANCE scene=%d source=%s license=%s',
        scene_order,
        attribution.source_url,
        attribution.license,
    )


def _verify_scenes(
    scenario: Scenario,
    manifest: AttributionManifest,
) -> None:
    """Check one authentic photo per scene, not just one per movie."""
    attributions: dict[int, SceneAttribution] = {
        attribution.scene_order: attribution for attribution in manifest.root
    }
    if len(attributions) != len(scenario.scenes):
        raise ValueError('Missing or duplicate photo attribution')
    if len(manifest.root) != len(scenario.scenes):
        raise ValueError('Unexpected number of photo attributions')
    catalog = InMemoryMemeRepository.from_json(CATALOG)
    position: float = 0
    duration: int = GenerationSettings().context_duration_seconds
    for scene in scenario.scenes:
        _verify_attribution(
            scene.order,
            scene.image_query,
            attributions.get(scene.order),
        )
        _verify_photo_frame(position + duration / 2, scene.order)
        position += (
            duration
            + probe_clip(
                catalog.get(scene.meme_id).video_path
            ).duration_seconds
        )
    LOGGER.info('ALL_SCENES_CONTAIN_PHOTOS=%d', len(scenario.scenes))


def main() -> None:
    """Verify provenance and an actual photographic frame for every scene."""
    scenario: Scenario = Scenario.model_validate_json(
        OUTPUT.with_suffix('.scenario.json').read_text(encoding='utf-8')
    )
    manifest: AttributionManifest = AttributionManifest.model_validate_json(
        OUTPUT.with_suffix('.attribution.json').read_text(encoding='utf-8')
    )
    _verify_scenes(scenario, manifest)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
