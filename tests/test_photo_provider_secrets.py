"""Check that external photo API keys never leak into YAML or logs."""

from pathlib import Path

import pytest

from meme_generator.config.loader import load_settings

CONFIG_NAME = 'config.yaml'
TEXT_ENCODING = 'utf-8'
ENVIRONMENT_ERROR = 'environment'

def test_pexels_credentials_rejected_in_yaml(tmp_path: Path) -> None:
    """The Pexels key must come from the environment, never from YAML."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'pexels:\n' '  api_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match=ENVIRONMENT_ERROR):
        load_settings(path)


def test_pexels_key_is_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment-provided API keys are masked in settings repr."""
    monkeypatch.setenv('MEMEGEN_PEXELS__API_KEY', 'secret-value')
    settings = load_settings(None)
    assert settings.pexels.api_key is not None
    assert settings.pexels.api_key.get_secret_value() == 'secret-value'
    assert 'secret-value' not in repr(settings)


def test_unsplash_credentials_rejected_in_yaml(tmp_path: Path) -> None:
    """The Unsplash access key is only read from the environment."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'unsplash:\n' '  access_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match=ENVIRONMENT_ERROR):
        load_settings(path)


def test_unsplash_access_key_masked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not reveal access keys in Pydantic settings representations."""
    monkeypatch.setenv('MEMEGEN_UNSPLASH__ACCESS_KEY', 'unsplash-secret')
    settings = load_settings(None)
    assert settings.unsplash.access_key is not None
    assert settings.unsplash.access_key.get_secret_value() == 'unsplash-secret'
    assert 'unsplash-secret' not in repr(settings)
