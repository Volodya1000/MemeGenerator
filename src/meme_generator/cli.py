"""Typer commands and dependency composition for video generation."""

from pathlib import Path
from typing import Annotated

import typer

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.ports.image_provider import ImageProvider
from meme_generator.application.ports.scenario_planner import ScenarioPlanner
from meme_generator.config.loader import llm_api_key, load_settings
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.commons import CommonsImageProvider
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.litellm_planner import LiteLLMPlanner
from meme_generator.infrastructure.rendering import FFmpegRenderer

app = typer.Typer(help='Generate short, themed reaction videos.')


@app.callback()
def application() -> None:
    """Video generation commands."""


def create_planner(settings: GenerationSettings) -> ScenarioPlanner:
    """Select an offline or LLM-powered scenario planner."""
    if settings.planner == 'demo':
        return DemoPlanner()
    if not settings.model:
        raise ValueError('Configure a model for LLM scenario planning')
    return LiteLLMPlanner(
        model=settings.model,
        api_base=settings.api_base,
        api_key=llm_api_key(),
    )


def create_images(settings: GenerationSettings) -> ImageProvider:
    """Use either an explicit local directory or licensed Commons."""
    if settings.images == 'commons':
        return CommonsImageProvider()
    if settings.image_dir is None:
        raise ValueError('image_dir is required when images=local')
    return LocalImageProvider(settings.image_dir.resolve())


@app.command()
def generate(
    topic: Annotated[str, typer.Option(help='Video theme or situation.')],
    config: Annotated[Path | None, typer.Option(help='YAML settings file.')] = None,
    scenes: Annotated[int | None, typer.Option(min=1)] = None,
    catalog: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    planner: Annotated[str | None, typer.Option()] = None,
    images: Annotated[str | None, typer.Option()] = None,
    image_dir: Annotated[Path | None, typer.Option()] = None,
    model: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Generate one complete MP4 and source-attribution manifests."""
    settings = load_settings(config)
    overrides: dict[str, object] = {
        key: value
        for key, value in {
            'scenes': scenes,
            'catalog': catalog,
            'output': output,
            'planner': planner,
            'images': images,
            'image_dir': image_dir,
            'model': model,
        }.items()
        if value is not None
    }
    settings = GenerationSettings.model_validate(
        {**settings.model_dump(), **overrides}
    )
    pipeline = GenerationPipeline(
        catalog=MemeCatalog.from_json(settings.catalog),
        planner=create_planner(settings),
        image_provider=create_images(settings),
        renderer=FFmpegRenderer(),
    )
    video = pipeline.generate(topic, settings.scenes, settings.output)
    typer.echo(f'Generated {video.scene_count} scenes: {video.output_path}')


def main() -> None:
    """Invoke CLI with a stable console entrypoint."""
    app()
