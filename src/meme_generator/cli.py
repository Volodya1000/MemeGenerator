"""CLI for the fully assembled meme-generation workflow."""

import argparse
import os
import sys
from pathlib import Path

from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.planning import DemoPlanner, OpenAIPlanner
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.commons import CommonsImageProvider
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.rendering import FFmpegRenderer


def configure_inputs(parser: argparse.ArgumentParser) -> None:
    """Register the topic, asset catalog and media destination flags."""
    parser.add_argument('--topic', required=True)
    parser.add_argument('--scenes', type=int, default=5)
    parser.add_argument(
        '--catalog', type=Path, default=Path('assets/memes.json')
    )
    parser.add_argument(
        '--output', type=Path, default=Path('output/result.mp4')
    )
    parser.add_argument(
        '--images', choices=('commons', 'local'), default='commons'
    )
    parser.add_argument('--image-dir', type=Path)


def configure_planner(parser: argparse.ArgumentParser) -> None:
    """Register semantic model options without storing API secrets."""
    parser.add_argument('--planner', choices=('llm', 'demo'), default='llm')
    parser.add_argument(
        '--base-url',
        default=os.getenv('MEMEGEN_BASE_URL', 'http://localhost:11434/v1'),
    )
    parser.add_argument('--model', default=os.getenv('MEMEGEN_MODEL', ''))


def build_parser() -> argparse.ArgumentParser:
    """Declare an explicit generate subcommand."""
    parser = argparse.ArgumentParser(prog='meme-generator')
    commands = parser.add_subparsers(dest='command', required=True)
    generate = commands.add_parser('generate', help='Generate one video')
    configure_inputs(generate)
    configure_planner(generate)
    return parser


def create_planner(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> DemoPlanner | OpenAIPlanner:
    """Choose between deterministic test mode and real inference."""
    if args.planner == 'demo':
        return DemoPlanner()
    if not args.model:
        parser.error('Specify --model or MEMEGEN_MODEL for LLM planning')
    return OpenAIPlanner(
        base_url=args.base_url,
        model=args.model,
        api_key=os.getenv('OPENAI_API_KEY', 'not-needed'),
    )


def create_images(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> CommonsImageProvider | LocalImageProvider:
    """Choose licensed Commons search or explicitly supplied pictures."""
    if args.images == 'local':
        if args.image_dir is None:
            parser.error('--image-dir is required for local images')
        return LocalImageProvider(args.image_dir.resolve())
    return CommonsImageProvider()


def main() -> None:
    """Build all components and run one synchronous generation request."""
    parser = build_parser()
    args = parser.parse_args()
    pipeline = GenerationPipeline(
        catalog=MemeCatalog.from_json(args.catalog),
        planner=create_planner(args, parser),
        image_provider=create_images(args, parser),
        renderer=FFmpegRenderer(),
    )
    video = pipeline.generate(args.topic, args.scenes, args.output)
    sys.stdout.write(
        f'Generated {video.scene_count} scenes: {video.output_path}\n'
    )
