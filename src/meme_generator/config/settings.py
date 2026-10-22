"""Root settings tree loaded from the environment and YAML."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from meme_generator.config.database import DatabaseSettings
from meme_generator.config.llm import LLMSettings


MAX_CONTEXT_DURATION_SECONDS = 15


class GenerationSettings(BaseSettings):
    """Root Pydantic Settings object for the entire application."""

    model_config = SettingsConfigDict(
        extra='forbid',
        env_prefix='MEMEGEN_',
        env_nested_delimiter='__',
        env_file='.env',
        nested_model_default_partial_update=True,
    )

    planner: Literal['llm', 'demo'] = 'llm'
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    scenes: int = Field(default=5, ge=1)
    context_duration_seconds: int = Field(
        default=5, ge=1, le=MAX_CONTEXT_DURATION_SECONDS
    )
    catalog: Path = Path('assets/catalog.json')
    output: Path = Path('output/result.mp4')
    images: Literal['commons', 'local', 'cards'] = 'commons'
    image_dir: Path | None = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Explicit precedence: env, dotenv, supplied YAML, file secrets."""
        return (
            env_settings,
            dotenv_settings,
            init_settings,
            file_secret_settings,
        )
