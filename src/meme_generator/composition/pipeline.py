"""Compose video generation at the outer application boundary."""

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.protocols.image_provider import (
    ImageProviderProtocol,
)
from meme_generator.application.protocols.scenario_planner import (
    ScenarioPlannerProtocol,
)
from meme_generator.composition.catalog import create_catalog
from meme_generator.config.settings import GenerationSettings
from meme_generator.domain.slide_mode import SlideMode
from meme_generator.infrastructure.captioned_images import (
    CaptionedImageProvider,
)
from meme_generator.infrastructure.caption_cards import (
    CaptionCardImageProvider,
)
from meme_generator.infrastructure.commons import CommonsImageProvider
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.llm.planner import LiteLLMPlanner


def create_planner(settings: GenerationSettings) -> ScenarioPlannerProtocol:
    """Select the deterministic or provider-neutral planning adapter."""
    if settings.planner == 'demo':
        return DemoPlanner()
    if not settings.llm.model:
        raise ValueError('Configure llm.model for scenario planning')
    api_key = settings.llm.api_key
    return LiteLLMPlanner(
        model=settings.llm.model,
        api_base=settings.llm.api_base,
        api_key=api_key.get_secret_value() if api_key else None,
        retry_attempts=settings.llm.retry_attempts,
    )


def create_images(settings: GenerationSettings) -> ImageProviderProtocol:
    """Compose real photos, text cards or photos with visible captions."""
    if settings.slide_mode == SlideMode.TEXT_ONLY:
        return CaptionCardImageProvider()
    if settings.images == 'cards':
        raise ValueError('Choose commons or local for image slide modes')
    if settings.images == 'commons':
        source: ImageProviderProtocol = CommonsImageProvider()
    elif settings.image_dir is not None:
        source = LocalImageProvider(settings.image_dir.resolve())
    else:
        raise ValueError('image_dir is required when images=local')
    if settings.slide_mode == SlideMode.IMAGE_WITH_CAPTION:
        return CaptionedImageProvider(source)
    return source


def create_pipeline(settings: GenerationSettings) -> GenerationPipeline:
    """Create a fully configured application pipeline."""
    return GenerationPipeline(
        catalog=create_catalog(settings),
        planner=create_planner(settings),
        image_provider=create_images(settings),
        renderer=FFmpegRenderer(settings.context_duration_seconds),
    )
