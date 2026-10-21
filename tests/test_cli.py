"""Typer exposes a stable documented command-line contract."""

from typer.testing import CliRunner

from meme_generator.cli import app


def test_cli_help_has_generate_command() -> None:
    """Discoverability should not depend on implementation details."""
    result = CliRunner().invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'generate' in result.output


def test_generate_help_exposes_config_file() -> None:
    """CLI documents a YAML configuration input."""
    result = CliRunner().invoke(app, ['generate', '--help'])
    assert result.exit_code == 0
    assert '--config' in result.output
