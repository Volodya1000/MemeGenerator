"""Explicit CLI command for relational reaction catalog imports."""

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
    """Import validated reactions and report the committed count."""
    settings = load_settings(config)
    imported: int = import_catalog_file(source or settings.catalog, settings)
    typer.echo(f'Imported {imported} reactions')
