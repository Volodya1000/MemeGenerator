"""Typer exposes a stable, discoverable command-line contract."""

from typer.testing import CliRunner

from meme_generator.cli import app


def test_cli_help_has_generate_command() -> None:
    """The root CLI documents the video-generation workflow."""
    invocation = CliRunner().invoke(app, ['--help'])
    assert invocation.exit_code == 0
    assert 'generate' in invocation.output


def test_generate_help_exposes_config_file() -> None:
    """The user can discover YAML configuration support."""
    invocation = CliRunner().invoke(app, ['generate', '--help'])
    assert invocation.exit_code == 0
    assert '--config' in invocation.output
