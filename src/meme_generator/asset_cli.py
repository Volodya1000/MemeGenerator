"""Command-line import of externally sourced reaction clips."""

import argparse
import logging
import subprocess
from pathlib import Path

import httpx

from meme_generator.application.meme_importer import import_catalog

logger = logging.getLogger(__name__)
IMPORT_ERRORS = (
    OSError, ValueError, subprocess.SubprocessError, httpx.HTTPError,
)


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
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        catalog = import_catalog(
            manifest_path=arguments.manifest,
            project_root=arguments.project_root,
            allow_download=arguments.download,
            force=arguments.force,
        )
    except IMPORT_ERRORS:
        logger.exception('Meme import failed')
        return 1
    logger.info('Imported %d reaction clips.', len(catalog))
    return 0
