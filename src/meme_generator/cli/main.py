"""Small Typer interface: detailed options live in validated YAML."""

from pathlib import Path
from typing import Annotated

import typer

from meme_generator.application.scene_budget import (
    MAX_TARGET_SECONDS,
    MIN_TARGET_SECONDS,
    estimate_scene_count,
)
from meme_generator.cli.catalog import catalog_app
from meme_generator.cli.demo import demo
from meme_generator.composition.catalog import create_catalog
from meme_generator.composition.pipeline import create_pipeline
from meme_generator.config.loader import load_settings
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.ffmpeg.settings import (
    IMAGE_DURATION_SECONDS,
)
from meme_generator.infrastructure.media_probe import probe_clip

app = typer.Typer(help='Generate short, themed reaction videos.')
app.add_typer(catalog_app, name='catalog')
app.command()(demo)


@app.callback()
def application() -> None:
    """Run a video-generation command."""


def calculate_scene_budget(
    settings: GenerationSettings,
    target_seconds: int,
) -> int:
    """Estimate from actual catalog video durations, never guessed constants."""
    durations = [
        probe_clip(meme.video_path).duration_seconds
        for meme in create_catalog(settings).all()
    ]
    return estimate_scene_count(target_seconds, durations, IMAGE_DURATION_SECONDS)


@app.command()
def generate(
    topic: Annotated[str, typer.Option(help='Video theme or situation.')],
    config: Annotated[
        Path | None, typer.Option(help='YAML settings file.')
    ] = None,
    scenes: Annotated[int | None, typer.Option(min=1)] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    target_seconds: Annotated[
        int | None,
        typer.Option(min=MIN_TARGET_SECONDS, max=MAX_TARGET_SECONDS),
    ] = None,
) -> None:
    """Generate one MP4 and its source manifests."""
    if scenes is not None and target_seconds is not None:
        raise typer.BadParameter('Use scenes OR target seconds, not both')
    settings = load_settings(config)
    overrides: dict[str, object] = {}
    if target_seconds is not None:
        overrides['scenes'] = calculate_scene_budget(settings, target_seconds)
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
