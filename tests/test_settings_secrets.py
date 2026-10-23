undefined

def test_unsplash_credentials_rejected_in_yaml(tmp_path: Path) -> None:
    """The Unsplash access key is only read from the environment."""
    path = tmp_path / CONFIG_NAME
    path.write_text(
        'unsplash:\n  access_key: do-not-commit\n',
        encoding=TEXT_ENCODING,
    )
    with pytest.raises(ValueError, match='environment'):
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
