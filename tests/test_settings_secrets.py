"""Security of configuration credentials at the YAML/environment boundary."""

from pathlib import Path

import pytest

from meme_generator.config.loader import load_settings
from meme_generator.config.settings import GenerationSettings

CONFIG_NAME = 'config.yaml'
TEXT_ENCODING = 'utf-8'
ENVIRONMENT_ERROR = 'environment'


def test_yaml_rejects_database_credentials(
    tmp_path: Path,
) -> None:
    """Only environment sources may provide a database credential."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'database:\n  url: sqlite:///secrets.db\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match=ENVIRONMENT_ERROR):
        load_settings(path)


def test_llm_credentials_are_not_allowed_in_yaml(tmp_path: Path) -> None:
    """A provider key in a config file is a configuration mistake."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'llm:\n  api_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match=ENVIRONMENT_ERROR):
        load_settings(path)


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


