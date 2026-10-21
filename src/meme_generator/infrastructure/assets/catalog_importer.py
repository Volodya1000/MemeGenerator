"""Assemble an atomic meme catalog from verified local clips."""

import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from meme_generator.domain.meme import Meme
from meme_generator.domain.meme_sources import MemeSources
from meme_generator.infrastructure.assets.clip_importer import import_meme

CATALOG_FILENAME = Path('assets/catalog.json')


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
            TypeAdapter(list[Meme]).dump_json(
                catalog, indent=2, ensure_ascii=False
            ).decode('utf-8'),
            encoding='utf-8',
        )
        temporary.replace(output)
    return catalog
