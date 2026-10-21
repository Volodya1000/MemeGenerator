"""Small Typer interface: detailed options live in validated YAML."""

from pathlib import Path
from typing import Annotated

import typer

from meme_generator.bootstrap import create_pipeline
from meme_generator.cli_catalog import catalog_app
from meme_generator.cli_demo import demo
from meme_generator.config.loader import load_settings
from meme_generator.config.settings import GenerationSettings

app = typer.Typer(help='Generate short, themed reaction videos.')
app.add_typer(catalog_app, name='catalog')
app.command()(demo)


@app.callback()
def application() -> None:
    """Run a video-generation command."""


@app.command()
def generate(
    topic: Annotated[str, typer.Option(help='Video theme or situation.')],
    config: Annotated[
        Path | None, typer.Option(help='YAML settings file.')
    ] = None,
    scenes: Annotated[int | None, typer.Option(min=1)] = None,
    output: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Generate one MP4 and its source manifests."""
    settings = load_settings(config)
    overrides: dict[str, object] = {}
    if scenes is not None:
        overrides['scenes'] = scenes
    if output is not None:
        overrides['output'] = output
    settings = GenerationSettings.model_validate(
        {**settings.model_dump(), **overrides}
    )
    video = create_pipeline(settings).generate(
        topic, settings.scenes, settings.output
    )
    typer.echo(f'Generated {video.scene_count} scenes: {video.output_path}')


def main() -> None:
    """Invoke the Typer CLI using the console entrypoint."""
    app()
