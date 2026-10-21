"""Load type-checked YAML via Pydantic Settings without exposing secrets."""

from collections.abc import Mapping
from pathlib import Path

from pydantic import TypeAdapter
from pydantic_settings import YamlConfigSettingsSource

from meme_generator.config.settings import GenerationSettings

_YAML_MAPPING = TypeAdapter(dict[str, object])
_ENVIRONMENT_ONLY_FIELDS: Mapping[str, frozenset[str]] = {
    'database': frozenset({'url'}),
    'llm': frozenset({'api_key'}),
}


def _validate_secret_sources(data: Mapping[str, object]) -> None:
    """Reject secrets in YAML even if an environment value overrides them."""
    for section_name, restricted_fields in _ENVIRONMENT_ONLY_FIELDS.items():
        section: object | None = data.get(section_name)
        if isinstance(section, dict):
            section_data: dict[str, object] = _YAML_MAPPING.validate_python(
                section
            )
            if restricted_fields.intersection(section_data):
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
    yaml_data: dict[str, object] = _YAML_MAPPING.validate_python(source())
    _validate_secret_sources(yaml_data)
    return GenerationSettings(**yaml_data)
