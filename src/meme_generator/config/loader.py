"""Load typed YAML with Pydantic Settings, no direct environment access."""

from pathlib import Path

from pydantic_settings import YamlConfigSettingsSource

from meme_generator.config.settings import GenerationSettings


def load_settings(path: Path | None) -> GenerationSettings:
    """Merge environment, dotenv, validated YAML, and defaults."""
    if path is None:
        return GenerationSettings()
    if not path.is_file():
        raise FileNotFoundError(path)
    source = YamlConfigSettingsSource(GenerationSettings, yaml_file=path)
    yaml_data: dict[str, object] = source()
    database = yaml_data.get('database')
    if isinstance(database, dict) and 'url' in database:
        raise ValueError('Database connection URL must be set via environment')
    llm = yaml_data.get('llm')
    if isinstance(llm, dict) and 'api_key' in llm:
        raise ValueError('LLM API key must be set via environment')
    return GenerationSettings(**yaml_data)
