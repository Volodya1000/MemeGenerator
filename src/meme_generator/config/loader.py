"""Read non-secret YAML settings and keep credentials in the environment."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from meme_generator.config.settings import GenerationSettings


def load_settings(path: Path | None) -> GenerationSettings:
    """Merge YAML and env overrides with validated defaults."""
    load_dotenv(dotenv_path=Path('.env'), override=False)
    raw: object = {}
    if path is not None:
        raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise TypeError('Configuration must contain a YAML mapping')
    config = dict(raw)
    model = os.getenv('MEMEGEN_MODEL')
    base_url = os.getenv('MEMEGEN_BASE_URL')
    if model is not None:
        config['model'] = model
    if base_url is not None:
        config['api_base'] = base_url
    return GenerationSettings.model_validate(config)


def database_url() -> str | None:
    """Read connection credentials without exposing them to YAML."""
    return os.getenv('MEMEGEN_DATABASE_URL')


def llm_api_key() -> str | None:
    """Never load or serialize API credentials from YAML."""
    return os.getenv('MEMEGEN_API_KEY') or os.getenv('OPENAI_API_KEY')
