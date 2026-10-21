"""Unit-level checks for local import and catalog consistency."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from meme_generator.application import meme_importer


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    """Write a single-clip source manifest with no remote dependency."""
    manifest_file = tmp_path / 'sources.json'
    manifest_file.write_text(
        json.dumps(
            {
                'schema_version': 1,
                'clips': [
                    {
                        'meme_id': 'example',
                        'phrase': 'Example reaction',
                        'source_page': 'https://cutzo.ru/video/example',
                    },
                ],
            },
        ),
        encoding='utf-8',
    )
    return manifest_file


def test_missing_source_preserves_existing_catalog(
    tmp_path: Path,
    manifest: Path,
) -> None:
    """A missing copyrighted source must not erase the current catalog."""
    output = tmp_path / 'assets' / 'catalog.json'
    output.parent.mkdir(parents=True)
    output.write_text('previous catalog', encoding='utf-8')
    with pytest.raises(FileNotFoundError):
        meme_importer.import_catalog(manifest, tmp_path)
    assert output.read_text(encoding='utf-8') == 'previous catalog'


def test_import_produces_domain_compatible_catalog(
    tmp_path: Path,
    manifest: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful import saves phrase and relative media path."""
    raw = tmp_path / 'assets' / 'raw' / 'example.mp4'
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b'fixture')
    (tmp_path / 'assets' / 'memes').mkdir()
    validation = Mock()
    normalization = Mock(
        side_effect=lambda source, destination: destination.write_bytes(b'mp4'),
    )
    monkeypatch.setattr(meme_importer, 'check_source', validation)
    monkeypatch.setattr(meme_importer, 'normalize_media', normalization)
    catalog = meme_importer.import_catalog(manifest, tmp_path)
    records = json.loads(
        (tmp_path / 'assets' / 'catalog.json').read_text(encoding='utf-8'),
    )
    assert len(catalog) == 1
    assert records == [
        {
            'meme_id': 'example',
            'phrase': 'Example reaction',
            'video_path': 'assets/memes/example.mp4',
        },
    ]
    assert validation.call_count == 1
    assert normalization.call_count == 1


def test_reimport_reuses_verified_files(
    tmp_path: Path,
    manifest: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A second run need not re-encode unchanged video files."""
    raw = tmp_path / 'assets' / 'raw' / 'example.mp4'
    ready = tmp_path / 'assets' / 'memes' / 'example.mp4'
    raw.parent.mkdir(parents=True)
    ready.parent.mkdir(parents=True)
    raw.write_bytes(b'input')
    ready.write_bytes(b'output')
    validation = Mock()
    normalization = Mock()
    monkeypatch.setattr(meme_importer, 'check_source', validation)
    monkeypatch.setattr(meme_importer, 'verify_normalized', validation)
    monkeypatch.setattr(meme_importer, 'normalize_media', normalization)
    meme_importer.import_catalog(manifest, tmp_path)
    normalization.assert_not_called()
    assert validation.call_count == 2
