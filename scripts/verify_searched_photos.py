"""Verify that the generated video includes genuine searched photographs."""

import logging
from pathlib import Path

from meme_generator.domain.attribution import (
    AttributionManifest,
    SceneAttribution,
)

MANIFEST = Path('output/gemini-result.attribution.json')
TEXT_CARD_LICENSE = 'Original generated typography'
LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Reject successful acceptance if every search fell back to typography."""
    manifest: AttributionManifest = AttributionManifest.model_validate_json(
        MANIFEST.read_text(encoding='utf-8')
    )
    photos: list[SceneAttribution] = [
        attribution for attribution in manifest.root
        if attribution.license != TEXT_CARD_LICENSE
    ]
    LOGGER.info('ACTUAL_PHOTOS_FOUND=%d', len(photos))
    for photo in photos:
        LOGGER.info(
            'PHOTO_PROVENANCE scene=%d source=%s license=%s',
            photo.scene_order,
            photo.source_url,
            photo.license,
        )
    if not photos:
        raise ValueError('No real searched photos were rendered')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    main()
