"""Thin Typer command for importing an approved JSON catalog into SQL."""

from pathlib import Path
from typing import Annotated

import typer

from meme_generator.composition.catalog import import_catalog_file
from meme_generator.config.loader import load_settings

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
    """Import and report a transactionally replaced catalog."""
    settings = load_settings(config)
    imported = import_catalog_file(source or settings.catalog)
    typer.echo(f'Imported {imported} reactions')
