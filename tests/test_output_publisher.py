"""Behavioral tests for successful and interrupted output publication."""

from collections.abc import Callable
from pathlib import Path

import pytest

from meme_generator.application.output_artifacts import OutputArtifacts
from meme_generator.application.output_publisher import publish_bundle

NEW_BYTES = b'new'
OLD_BYTES = b'old'
VIDEO_NAME = 'result.mp4'


class InterruptReplacement:
    """Simulate one OS-level rename failure without mocking use-case calls."""

    def __init__(self, source: Path, destination: Path) -> None:
        """Save the external filesystem operation and failure target."""
        self._source = source
        self._destination = destination
        self._original: Callable[[Path, Path], Path] = Path.replace

    def __call__(self, source: Path, destination: Path) -> Path:
        """Fail only when the staged video is about to become visible."""
        if source == self._source and destination == self._destination:
            raise OSError('disk rename failed')
        return self._original(source, destination)


def write_bundle(video: Path, payload: bytes) -> None:
    """Create three existing files representing a coherent generation."""
    video.parent.mkdir(parents=True, exist_ok=True)
    for artifact in OutputArtifacts.from_video(video).publication_order():
        artifact.write_bytes(payload)


def test_complete_bundle_is_published(tmp_path: Path) -> None:
    """Successful publication replaces video and both manifests."""
    staged = tmp_path / 'stage' / VIDEO_NAME
    final = tmp_path / VIDEO_NAME
    write_bundle(staged, NEW_BYTES)
    write_bundle(final, OLD_BYTES)
    publish_bundle(staged, final)
    for artifact in OutputArtifacts.from_video(final).publication_order():
        assert artifact.read_bytes() == NEW_BYTES


def test_rename_failure_restores_all_old_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An interrupted final rename restores the prior coherent state."""
    staged = tmp_path / 'stage' / VIDEO_NAME
    final = tmp_path / VIDEO_NAME
    write_bundle(staged, NEW_BYTES)
    write_bundle(final, OLD_BYTES)
    monkeypatch.setattr(Path, 'replace', InterruptReplacement(staged, final))
    with pytest.raises(OSError, match='rename failed'):
        publish_bundle(staged, final)
    for artifact in OutputArtifacts.from_video(final).publication_order():
        assert artifact.read_bytes() == OLD_BYTES


def test_missing_manifest_preserves_outputs(tmp_path: Path) -> None:
    """No old artifact is touched if any staged manifest is missing."""
    staged = tmp_path / 'stage' / VIDEO_NAME
    final = tmp_path / VIDEO_NAME
    write_bundle(staged, NEW_BYTES)
    write_bundle(final, OLD_BYTES)
    staged.with_suffix('.attribution.json').unlink()
    with pytest.raises(FileNotFoundError):
        publish_bundle(staged, final)
    for artifact in OutputArtifacts.from_video(final).publication_order():
        assert artifact.read_bytes() == OLD_BYTES
