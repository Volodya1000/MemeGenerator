"""Import verified media into the local catalog without distributing it."""

import json
from pathlib import Path

from meme_generator.domain.meme_sources import MemeSource, MemeSources
from meme_generator.domain.models import Meme
from meme_generator.infrastructure.meme_media import (
    check_source,
    download_media,
    normalize_media,
    verify_normalized,
)


def import_meme(
    source: MemeSource,
    project_root: Path,
    *,
    allow_download: bool,
    force: bool,
) -> Meme:
    """Prepare one clip, with explicit permission for network fetching."""
    raw = project_root / 'assets' / 'raw' / f'{source.meme_id}.mp4'
    ready = project_root / 'assets' / 'memes' / f'{source.meme_id}.mp4'
    if not raw.is_file():
        if not allow_download or source.media_url is None:
            raise FileNotFoundError(
                f'Missing {raw}. Download it from {source.source_page} '
                'or configure media_url and pass --download.',
            )
        download_media(source.media_url, raw)
    check_source(raw, source.sha256)
    if force or not ready.is_file() or raw.stat().st_mtime_ns > ready.stat().st_mtime_ns:
        normalize_media(raw, ready)
    else:
        verify_normalized(ready)
    return Meme(
        meme_id=source.meme_id,
        phrase=source.phrase,
        video_path=Path('assets') / 'memes' / f'{source.meme_id}.mp4',
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
            source, project_root, allow_download=allow_download, force=force,
        )
        for source in manifest.clips
    ]
    output = project_root / 'assets' / 'catalog.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.json.tmp')
    try:
        contents = [meme.model_dump(mode='json') for meme in catalog]
        temporary.write_text(
            json.dumps(contents, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return catalog
