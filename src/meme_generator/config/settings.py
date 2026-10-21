"""One typed configuration tree for environment and YAML settings."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class DatabaseSettings(BaseModel):
    """Storage configuration, with connection credentials kept secret."""

    model_config = ConfigDict(extra='forbid')

    backend: Literal['json', 'sqlalchemy'] = 'json'
    url: SecretStr | None = None


class LLMSettings(BaseModel):
    """Model provider configuration and bounded transient retries."""

    model_config = ConfigDict(extra='forbid')

    model: str = ''
    api_base: str | None = None
    api_key: SecretStr | None = None
    retry_attempts: int = Field(default=3, ge=1, le=10)


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
