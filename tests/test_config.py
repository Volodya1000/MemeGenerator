"""Test complete typed configuration and source precedence."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from meme_generator.config.loader import load_settings
from meme_generator.config.settings import GenerationSettings

CONFIG_NAME = 'config.yaml'
TEXT_ENCODING = 'utf-8'


def test_yaml_settings_are_loaded(tmp_path: Path) -> None:
    """Explicit YAML config supplies valid non-secret defaults."""
    path = tmp_path / CONFIG_NAME
    path.write_text('planner: demo\nscenes: 2\n', encoding=TEXT_ENCODING)
    settings: GenerationSettings = load_settings(path)
    assert settings.planner == 'demo'
    assert settings.scenes == 2


def test_unknown_config_key_fails(tmp_path: Path) -> None:
    """Unknown settings cannot be hidden by YAML normalization."""
    path = tmp_path / CONFIG_NAME
    path.write_text('does_not_exist: true\n', encoding=TEXT_ENCODING)
    with pytest.raises(ValidationError):
        load_settings(path)


def test_invalid_scene_count_fails(tmp_path: Path) -> None:
    """Invalid values are rejected before any generation begins."""
    path = tmp_path / CONFIG_NAME
    path.write_text('scenes: -3\n', encoding=TEXT_ENCODING)
    with pytest.raises(ValidationError):
        load_settings(path)


def test_nested_environment_overrides_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Environment values override typed nested YAML values."""
    monkeypatch.setenv('MEMEGEN_LLM__MODEL', 'openai/override')
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'llm:\n  model: openai/previous\n',
        encoding=TEXT_ENCODING,
    )
    assert load_settings(path).llm.model == 'openai/override'


def test_nested_database_yaml_and_paths(tmp_path: Path) -> None:
    """Nested storage settings and local paths parse correctly."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'catalog: assets/memes.json\n'
        'output: output/result.mp4\n'
        'database:\n  backend: sqlalchemy\n',
        encoding=TEXT_ENCODING,
    )
    settings: GenerationSettings = load_settings(path)
    assert settings.catalog == Path('assets/memes.json')
    assert settings.output == Path('output/result.mp4')
    assert settings.database.backend == 'sqlalchemy'
