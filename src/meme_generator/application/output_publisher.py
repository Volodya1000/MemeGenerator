"""Recoverable multi-file publication at the application I/O boundary."""

from pathlib import Path
from tempfile import TemporaryDirectory

from meme_generator.application.output_artifacts import OutputArtifacts


class PublicationTransaction:
    """Remember old artifacts so interrupted writes can be rolled back."""

    def __init__(self, backup_dir: Path) -> None:
        """Initialize publication state and private rollback backups."""
        self._backup_dir = backup_dir
        self._originals: list[tuple[Path, Path]] = []
        self._published: list[Path] = []

    def publish(self, source: Path, target: Path) -> None:
        """Safeguard an old file before installing its staged replacement."""
        if target.exists():
            backup = self._backup_dir / target.name
            target.replace(backup)
            self._originals.append((backup, target))
        source.replace(target)
        self._published.append(target)

    def publish_all(
        self,
        staged: OutputArtifacts,
        target: OutputArtifacts,
    ) -> None:
        """Publish each artifact in the expected order."""
        for source, destination in zip(
            staged.publication_order(),
            target.publication_order(),
            strict=True,
        ):
            self.publish(source, destination)

    def rollback(self) -> None:
        """Restore the prior files after a failed publish operation."""
        for output in reversed(self._published):
            output.unlink(missing_ok=True)
        for backup, original in reversed(self._originals):
            backup.replace(original)


def publish_bundle(staged_video: Path, final_video: Path) -> None:
    """Install all generation files, rolling back on I/O failures."""
    staged = OutputArtifacts.from_video(staged_video)
    for source in staged.publication_order():
        if not source.is_file():
            raise FileNotFoundError(source)
    with TemporaryDirectory(
        prefix='memegen-backup-',
        dir=final_video.parent,
    ) as temporary:
        transaction = PublicationTransaction(Path(temporary))
        try:
            transaction.publish_all(
                staged,
                OutputArtifacts.from_video(final_video),
            )
        except OSError:
            transaction.rollback()
            raise
