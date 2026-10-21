"""Command-line import of externally sourced reaction clips."""

import argparse
import subprocess
import sys
from pathlib import Path

import httpx
from pydantic import ValidationError

from meme_generator.application.meme_importer import import_catalog


def main() -> int:
    """Prepare and validate a local catalog for the video generator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--manifest', type=Path, default=Path('assets/sources.json'),
    )
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--force', action='store_true')
    arguments = parser.parse_args()
    try:
        catalog = import_catalog(
            manifest_path=arguments.manifest,
            project_root=arguments.project_root,
            allow_download=arguments.download,
            force=arguments.force,
        )
    except (
        OSError, ValueError, httpx.HTTPError,
        subprocess.CalledProcessError, ValidationError,
    ) as error:
        print(f'Meme import failed: {error}', file=sys.stderr)
        return 1
    print(f'Imported {len(catalog)} reaction clips.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
