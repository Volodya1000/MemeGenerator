"""Self-contained local playback smoke test for imported reaction media."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

import typer

from meme_generator.composition.pipeline import create_pipeline
from meme_generator.config.database import DatabaseSettings
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.ffmpeg.demo_context import (
    create_demo_context,
)

DEFAULT_CATALOG = Path('assets/catalog.json')
DEFAULT_OUTPUT = Path('output/demo.mp4')


def demo(
    catalog: Annotated[
        Path, typer.Option(help='Validated local reaction catalog.')
    ] = DEFAULT_CATALOG,
    output: Annotated[
        Path, typer.Option(help='Destination MP4 for the demo.')
    ] = DEFAULT_OUTPUT,
    topic: Annotated[
        str, typer.Option(help='Demo reaction theme.')
    ] = 'Local demo',
) -> None:
    """Generate one playable reaction from local catalog without LLM or web."""
    with TemporaryDirectory(prefix='memegen-demo-images-') as temporary:
        image_dir = Path(temporary)
        create_demo_context(image_dir / '1.png')
        settings = GenerationSettings().model_copy(
            update={
                'planner': 'demo',
                'database': DatabaseSettings(backend='json'),
                'images': 'local',
                'image_dir': image_dir,
                'catalog': catalog,
                'scenes': 1,
                'output': output,
            }
        )
        video = create_pipeline(settings).generate(topic, 1, output)
    typer.echo(f'Demo video created: {video.output_path}')
