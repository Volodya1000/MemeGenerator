"""Import verified media into the local catalog without distributing it."""

import json
import tempfile
from pathlib import Path

from meme_generator.domain.meme_sources import MemeSource, MemeSources
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
CATALOG_FILENAME = ASSET_DIRECTORY / 'catalog.json'


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


def import_catalog(
    manifest_path: Path,
    project_root: Path,
    *,
    allow_download: bool = False,
    force: bool = False,
) -> list[Meme]:
    """Write a complete catalog only when every listed clip succeeds."""
    manifest = MemeSources.model_validate_json(
        manifest_path.read_text(encoding='utf-8'),
    )
    catalog = [
        import_meme(
            source,
            project_root,
            allow_download=allow_download,
            force=force,
        )
        for source in manifest.clips
    ]
    output = project_root / CATALOG_FILENAME
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        temporary = Path(directory) / 'catalog.json'
        temporary.write_text(
            json.dumps(
                [meme.model_dump(mode='json') for meme in catalog],
                ensure_ascii=False,
                indent=2,
            ),
            encoding='utf-8',
        )
        temporary.replace(output)
    return catalog
