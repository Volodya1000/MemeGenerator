"""One canonical path model for video and its JSON manifests."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OutputArtifacts:
    """Related output files published as one recoverable generation."""

    scenario: Path
    attribution: Path
    video: Path

    @classmethod
    def from_video(cls, video: Path) -> 'OutputArtifacts':
        """Derive exact companion manifest names only in this module."""
        return cls(
            scenario=video.with_suffix('.scenario.json'),
            attribution=video.with_suffix('.attribution.json'),
            video=video,
        )

    def publication_order(self) -> tuple[Path, Path, Path]:
        """Publish metadata before the final playable MP4 marker."""
        return self.scenario, self.attribution, self.video
