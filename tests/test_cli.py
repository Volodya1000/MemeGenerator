"""CLI tests focus on observable behavior, not Rich help formatting."""

from pathlib import Path

from typer.testing import CliRunner

from meme_generator.cli.main import app


def test_cli_help_has_generate_command() -> None:
    """The root CLI exposes its intended video workflow."""
    invocation = CliRunner().invoke(app, ['--help'])
    assert invocation.exit_code == 0
    assert 'generate' in invocation.output


def test_generate_accepts_yaml_config_argument(tmp_path: Path) -> None:
    """Config file paths are forwarded to the settings loader."""
    requested = tmp_path / 'missing.yaml'
    invocation = CliRunner().invoke(
        app,
        ['generate', '--topic', 'test', '--config', str(requested)],
    )
    assert isinstance(invocation.exception, FileNotFoundError)
    assert str(requested) in str(invocation.exception)
