"""Port for assembling complete playable videos."""

from pathlib import Path
from typing import Protocol

from meme_generator.application.protocols.meme_repository import (
    MemeRepositoryProtocol,
)
from meme_generator.domain.image_asset import ImageAsset
from meme_generator.domain.scenario import Scenario


class VideoRendererProtocol(Protocol):
    """Write a playable video according to the supplied scene order."""

    def render(
        self,
        scenario: Scenario,
        catalog: MemeRepositoryProtocol,
        images: list[ImageAsset],
        output_path: Path,
    ) -> Path:
        """Render a complete MP4 at the requested location."""
        ...
