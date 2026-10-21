"""Compose concrete adapters at the outer application boundary."""

from meme_generator.application.demo_planner import DemoPlanner
from meme_generator.application.pipeline import GenerationPipeline
from meme_generator.application.ports.image_provider import ImageProvider
from meme_generator.application.ports.meme_repository import MemeRepository
from meme_generator.application.ports.scenario_planner import ScenarioPlanner
from meme_generator.config.loader import database_url, llm_api_key
from meme_generator.config.settings import GenerationSettings
from meme_generator.infrastructure.catalog import MemeCatalog
from meme_generator.infrastructure.commons import CommonsImageProvider
from meme_generator.infrastructure.database.engine import create_catalog_engine
from meme_generator.infrastructure.database.repository import (
    SqlAlchemyMemeRepository,
)
from meme_generator.infrastructure.ffmpeg.renderer import FFmpegRenderer
from meme_generator.infrastructure.images import LocalImageProvider
from meme_generator.infrastructure.litellm_planner import LiteLLMPlanner


def create_planner(settings: GenerationSettings) -> ScenarioPlanner:
    """Choose between a deterministic and provider-neutral planner."""
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
    """Use an explicit local directory or Wikimedia Commons images."""
    if settings.images == 'commons':
        return CommonsImageProvider()
    if settings.image_dir is None:
        raise ValueError('image_dir is required when images=local')
    return LocalImageProvider(settings.image_dir.resolve())


def create_database_catalog() -> SqlAlchemyMemeRepository:
    """Connect to the configured SQL database, with no hidden fallback."""
    url = database_url()
    if not url:
        raise ValueError('Set MEMEGEN_DATABASE_URL for SQL catalog')
    return SqlAlchemyMemeRepository(create_catalog_engine(url))


def create_catalog(settings: GenerationSettings) -> MemeRepository:
    """Select a JSON or relational catalog via an application port."""
    if settings.catalog_backend == 'sqlalchemy':
        return create_database_catalog()
    return MemeCatalog.from_json(settings.catalog)


def create_pipeline(settings: GenerationSettings) -> GenerationPipeline:
    """Construct one generation use case with concrete I/O adapters."""
    return GenerationPipeline(
        catalog=create_catalog(settings),
        planner=create_planner(settings),
        image_provider=create_images(settings),
        renderer=FFmpegRenderer(),
    )
