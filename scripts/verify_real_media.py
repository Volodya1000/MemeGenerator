"""Check the real-media import on an ephemeral CI runner."""

import hashlib
import logging
from pathlib import Path

from pydantic import TypeAdapter

from meme_generator.domain.meme_sources import MemeSource, MemeSources
from meme_generator.domain.models import Meme
from meme_generator.infrastructure.meme_probe import (
    check_source,
    verify_normalized,
)

SOURCES_PATH = Path('assets/sources.json')
CATALOG_PATH = Path('assets/catalog.json')
RAW_DIRECTORY = Path('assets/raw')
READY_DIRECTORY = Path('assets/memes')
EXPECTED_CLIPS = 7

logger = logging.getLogger(__name__)


def verify_entry(meme: Meme, source: MemeSource) -> None:
    """Check provenance, catalog mapping, and final audio/video metadata."""
    expected = READY_DIRECTORY / f'{source.meme_id}.mp4'
    if meme.phrase != source.phrase or meme.video_path != expected:
        raise ValueError(f'Unexpected catalog mapping: {meme.meme_id}')
    check_source(RAW_DIRECTORY / f'{source.meme_id}.mp4', source.sha256)
    media = verify_normalized(meme.video_path)
    with meme.video_path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    logger.info(
        '%s duration=%s bytes=%s sha256=%s',
        meme.meme_id,
        media.format.duration,
        meme.video_path.stat().st_size,
        digest,
    )


def verify_catalog() -> None:
    """Require all seven verified entries without duplicates or omissions."""
    manifest = MemeSources.model_validate_json(
        SOURCES_PATH.read_text(encoding='utf-8'),
    )
    catalog = TypeAdapter(list[Meme]).validate_json(
        CATALOG_PATH.read_text(encoding='utf-8'),
    )
    expected = {source.meme_id: source for source in manifest.clips}
    found = {meme.meme_id for meme in catalog}
    if (
        len(expected) != EXPECTED_CLIPS
        or len(catalog) != EXPECTED_CLIPS
        or found != expected.keys()
    ):
        raise ValueError('The imported catalog must contain seven unique clips')
    for meme in catalog:
        verify_entry(meme, expected[meme.meme_id])
    logger.info('VERIFIED_REAL_CLIPS=%s', EXPECTED_CLIPS)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    verify_catalog()
