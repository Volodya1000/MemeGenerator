"""Security of configuration credentials at the YAML/environment boundary."""

from pathlib import Path

import pytest

from meme_generator.config.loader import load_settings
from meme_generator.config.settings import GenerationSettings

CONFIG_NAME = 'config.yaml'
TEXT_ENCODING = 'utf-8'


def test_yaml_rejects_database_credentials(
    tmp_path: Path,
) -> None:
    """Only environment sources may provide a database credential."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'database:\n  url: sqlite:///secrets.db\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match='environment'):
        load_settings(path)


def test_llm_credentials_are_not_allowed_in_yaml(tmp_path: Path) -> None:
    """A provider key in a config file is a configuration mistake."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'llm:\n  api_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match='environment'):
        load_settings(path)


def test_pexels_credentials_rejected_in_yaml(tmp_path: Path) -> None:
    """The Pexels key must come from the environment, never from YAML."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'pexels:\n  api_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match='environment'):
        load_settings(path)


def test_pexels_key_is_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment-provided API keys are masked in settings repr."""
    monkeypatch.setenv('MEMEGEN_PEXELS__API_KEY', 'secret-value')
    settings = load_settings(None)
    assert settings.pexels.api_key is not None
    assert settings.pexels.api_key.get_secret_value() == 'secret-value'
    assert 'secret-value' not in repr(settings)


def test_secret_values_are_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default model representation must never reveal database passwords."""
    monkeypatch.setenv(
        'MEMEGEN_DATABASE__URL', 'postgresql://user:secret@localhost/db'
    )
    settings: GenerationSettings = load_settings(None)
    assert 'secret@' not in repr(settings)
    assert settings.database.url is not None
    assert 'secret@' in settings.database.url.get_secret_value()


def test_missing_explicit_yaml_is_rejected(tmp_path: Path) -> None:
    """A mistyped config path is not silently treated as defaults."""
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path / 'unknown.yaml')
