"""Load type-checked YAML via Pydantic Settings without exposing secrets."""

from collections.abc import Mapping
from pathlib import Path

from pydantic import TypeAdapter
from pydantic_settings import YamlConfigSettingsSource

from meme_generator.config.settings import GenerationSettings

_ENVIRONMENT_ONLY_FIELDS: tuple[tuple[str, str], ...] = (
    ('database', 'url'),
    ('llm', 'api_key'),
    ('pexels', 'api_key'),
)


def _validate_secret_sources(yaml_settings: Mapping[str, object]) -> None:
    """Reject secrets in YAML even if environment variables override them."""
    for section_name, restricted_field in _ENVIRONMENT_ONLY_FIELDS:
        section: object | None = yaml_settings.get(section_name)
        if isinstance(section, dict):
            section_data: dict[str, object] = TypeAdapter(
                dict[str, object]
            ).validate_python(section)
            if restricted_field in section_data:
                raise ValueError(
                    'Credentials must be configured through environment'
                )


def load_settings(path: Path | None) -> GenerationSettings:
    """Merge environment, dotenv, validated YAML, and defaults."""
    if path is None:
        return GenerationSettings()
    if not path.is_file():
        raise FileNotFoundError(path)
    source = YamlConfigSettingsSource(GenerationSettings, yaml_file=path)
    yaml_data = source()
    validated_yaml: dict[str, object] = TypeAdapter(
        dict[str, object]
    ).validate_python(yaml_data)
    _validate_secret_sources(validated_yaml)
    return GenerationSettings(**yaml_data)
