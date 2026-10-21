"""Import and normalize one curated reaction clip."""

from pathlib import Path

from meme_generator.domain.meme_sources import MemeSource
from meme_generator.domain.models import Meme
from meme_generator.infrastructure.meme_download import download_media
from meme_generator.infrastructure.meme_normalize import normalize_media
from meme_generator.infrastructure.meme_probe import (
    check_source,
    verify_normalized,
)

ASSET_DIRECTORY = Path('assets')
RAW_DIRECTORY = ASSET_DIRECTORY / 'raw'
MEDIA_DIRECTORY = ASSET_DIRECTORY / 'memes'


def _needs_normalization(raw: Path, ready: Path, *, force: bool) -> bool:
    """Rebuild missing, outdated, or explicitly invalidated outputs."""
    if force or not ready.is_file():
        return True
    return raw.stat().st_mtime_ns > ready.stat().st_mtime_ns


def import_meme(
    source: MemeSource,
    project_root: Path,
    *,
    allow_download: bool,
    force: bool,
) -> Meme:
    """Prepare one clip, with explicit permission for network fetching."""
    raw = project_root / RAW_DIRECTORY / f'{source.meme_id}.mp4'
    ready = project_root / MEDIA_DIRECTORY / f'{source.meme_id}.mp4'
    if not raw.is_file():
        if not allow_download or source.media_url is None:
            raise FileNotFoundError(
                f'Missing {raw}. Download it from {source.source_page} '
                'or configure media_url and pass --download.',
            )
        download_media(source.media_url, raw)
    check_source(raw, source.sha256)
    if _needs_normalization(raw, ready, force=force):
        normalize_media(raw, ready)
    else:
        verify_normalized(ready)
    return Meme(
        meme_id=source.meme_id,
        phrase=source.phrase,
        video_path=MEDIA_DIRECTORY / f'{source.meme_id}.mp4',
    )
