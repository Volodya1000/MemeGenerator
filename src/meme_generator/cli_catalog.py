"""Catalog import command, separate from generation CLI orchestration."""

from pathlib import Path
from typing import Annotated

import typer

from meme_generator.application.catalog_import import import_memes
from meme_generator.bootstrap import create_database_catalog
from meme_generator.config.loader import load_settings
from meme_generator.infrastructure.catalog import MemeCatalog

catalog_app = typer.Typer(help='Manage the reaction catalog.')


@catalog_app.command('import')
def import_catalog(
    config: Annotated[
        Path | None, typer.Option(help='Non-secret YAML configuration.')
    ] = None,
    source: Annotated[
        Path | None, typer.Option(help='Validated local JSON catalog.')
    ] = None,
) -> None:
    """Load approved clips into SQL in one transaction."""
    settings = load_settings(config)
    catalog = MemeCatalog.from_json(source or settings.catalog)
    repository = create_database_catalog()
    imported = import_memes(repository, catalog.all())
    typer.echo(f'Imported {imported} reactions')
