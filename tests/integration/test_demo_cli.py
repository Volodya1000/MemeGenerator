"""CLI-level acceptance with a real encoder and no external dependencies."""

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from meme_generator.cli.main import app
from meme_generator.infrastructure.media_probe import probe_clip

REACTION_ID = 'demo_reaction'
OUTPUT_NAME = 'demo.mp4'


def create_source_clip(directory: Path) -> Path:
    """Produce a legal synthetic clip with real audio and video tracks."""
    source = directory / 'source.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-loglevel',
            'error',
            '-y',
            '-f',
            'lavfi',
            '-i',
            'color=c=red:s=320x240:r=25',
            '-f',
            'lavfi',
            '-i',
            'sine=frequency=440:duration=0.7',
            '-t',
            '0.7',
            '-c:v',
            'mpeg4',
            '-c:a',
            'aac',
            str(source),
        ],
        capture_output=True,
        check=True,
    )
    return source


def prepare_demo_catalog(source: Path) -> Path:
    """Expose a catalog with relative paths exactly as users provide them."""
    catalog = source.parent / 'catalog.json'
    catalog.write_text(
        json.dumps(
            [
                {
                    'meme_id': REACTION_ID,
                    'phrase': 'Okay',
                    'video_path': source.name,
                }
            ],
        ),
        encoding='utf-8',
    )
    return catalog


@pytest.mark.integration
def test_demo_cli_creates_mp4_and_metadata(tmp_path: Path) -> None:
    """A single command produces video with audio and typed JSON manifests."""
    catalog = prepare_demo_catalog(create_source_clip(tmp_path))
    output = tmp_path / 'result' / OUTPUT_NAME
    invocation = CliRunner().invoke(
        app, ['demo', '--catalog', str(catalog), '--output', str(output)]
    )
    assert invocation.exit_code == 0, invocation.exception
    assert 'Demo video created:' in invocation.output
    assert probe_clip(output).has_audio
    assert output.with_suffix('.scenario.json').is_file()
    assert output.with_suffix('.attribution.json').is_file()
