"""Validate non-secret settings without contacting external services."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from meme_generator.config.loader import load_settings

CONFIG_NAME = 'config.yaml'
TEXT_ENCODING = 'utf-8'


def test_yaml_settings_are_loaded(tmp_path: Path) -> None:
    """Explicit YAML can change the default planning mode."""
    path = tmp_path / CONFIG_NAME
    path.write_text('planner: demo\nscenes: 2\n', encoding=TEXT_ENCODING)
    settings = load_settings(path)
    assert settings.planner == 'demo'
    assert settings.scenes == 2


def test_unknown_config_key_fails(tmp_path: Path) -> None:
    """Typos in YAML cannot be silently ignored."""
    path = tmp_path / CONFIG_NAME
    path.write_text('does_not_exist: true\n', encoding=TEXT_ENCODING)
    with pytest.raises(ValidationError):
        load_settings(path)


def test_invalid_scene_count_fails(tmp_path: Path) -> None:
    """A negative scene count is invalid before pipeline startup."""
    path = tmp_path / CONFIG_NAME
    path.write_text('scenes: -3\n', encoding=TEXT_ENCODING)
    with pytest.raises(ValidationError):
        load_settings(path)


def test_environment_overrides_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime model choices take precedence over checked-in YAML."""
    monkeypatch.setenv('MEMEGEN_MODEL', 'openai/override')
    path = tmp_path / CONFIG_NAME
    path.write_text('model: openai/previous\n', encoding=TEXT_ENCODING)
    assert load_settings(path).model == 'openai/override'
